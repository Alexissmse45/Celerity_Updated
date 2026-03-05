from flask import Flask, request, jsonify
from flask_cors import CORS
from lexer import Lexer
from CFG import LL1Parser, parse_table, follow_set, cfg
from semantic import Semantic
from code_gen import CodeGenerator
from tac_interpreter import TACInterpreter, count_inputs, get_input_types

app = Flask(__name__)
CORS(app)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data          = request.json
        code          = data.get('code', '')
        analysis_type = data.get('analysisType', 'all')

        if not code:
            return jsonify({'success': False, 'output': 'No code provided',
                            'errors': ['No code provided'], 'tokens': [],
                            'syntaxErrors': [], 'syntaxTree': None,
                            'semanticErrors': [], 'semanticInfo': None,
                            'activeAnalysis': None, 'tacCode': None,
                            'programEvents': []}), 400

        result = {
            'success': True, 'output': '', 'errors': [], 'tokens': [],
            'syntaxErrors': [], 'syntaxTree': None,
            'semanticErrors': [], 'semanticInfo': None,
            'activeAnalysis': analysis_type,
            'tacCode': None,
            'programEvents': [],
        }

        output_lines = []

        # ── PHASE 1: LEXICAL ─────────────────────────────────────────────────
        lexer = Lexer()
        tokens, lexer_errors = lexer.lexeme(code)
        if lexer_errors:
            result.update(success=False, errors=lexer_errors,
                          output='Running code...\n✗ Lexical analysis failed',
                          activeAnalysis='lexical',
                          tokens=[{'lexeme':t[0],'token':t[1],'line':t[2],'column':t[3]} for t in tokens])
            return jsonify(result)

        result['tokens'] = [{'lexeme':t[0],'token':t[1],'line':t[2],'column':t[3]} for t in tokens]
        output_lines += ['Running code...', '✓ Lexical analysis passed']

        if analysis_type == 'lexical':
            result.update(output='\n'.join(output_lines), activeAnalysis='lexical')
            return jsonify(result)
        #print("TOKENS:", [(t[0], t[1]) for t in tokens])#FOR TESTING HIHI
        # ── PHASE 2: SYNTAX ──────────────────────────────────────────────────
        parser = LL1Parser(cfg, parse_table, follow_set)
        parse_success, syntax_errors = parser.parse(tokens)
        if not parse_success:
            result.update(success=False, syntaxErrors=syntax_errors, errors=syntax_errors,
                          output='\n'.join(output_lines + ['✗ Syntax analysis failed']),
                          activeAnalysis='syntax')
            return jsonify(result)

        output_lines.append('✓ Syntax analysis passed')
        result['syntaxTree'] = {'message': 'Syntax analysis completed without errors', 'status': 'success'}

        if analysis_type == 'syntax':
            result.update(output='\n'.join(output_lines), activeAnalysis='syntax')
            return jsonify(result)

        # ── PHASE 3: SEMANTIC ────────────────────────────────────────────────
        try:
            sem        = Semantic()
            sem_errors = sem.semantic_analyzer(tokens)
            if sem_errors:
                result.update(success=False, semanticErrors=sem_errors, errors=sem_errors,
                              output='\n'.join(output_lines + ['✗ Semantic analysis failed']),
                              activeAnalysis='semantic')
                return jsonify(result)

            formatted_st = {}
            for scope, symbols in sem.symbol_table.items():
                formatted_st[scope] = {}
                for vn, sym in symbols.items():
                    formatted_st[scope][vn] = {
                        'name': sym.name, 'symbol_type': sym.symbol_type,
                        'data_type': sym.data_type, 'value': sym.value,
                        'is_const': sym.is_const, 'line': sym.line,
                        'column': sym.column, 'dimension': sym.dimension, 'sizes': sym.sizes
                    }
            result['semanticInfo'] = {'symbol_table': formatted_st, 'struct_table': sem.struct_table}
            output_lines.append('✓ Semantic analysis passed')

        except Exception as e:
            import traceback; traceback.print_exc()
            result.update(success=False,
                          semanticErrors=[f"Semantic error: {e}"], errors=[f"Semantic error: {e}"],
                          output='\n'.join(output_lines + ['✗ Semantic analysis failed']),
                          activeAnalysis='semantic')
            return jsonify(result)

        if analysis_type == 'semantic':
            result.update(output='\n'.join(output_lines), activeAnalysis='semantic')
            return jsonify(result)

        # ── PHASE 4: CODE GEN + RUN ──────────────────────────────────────────
        try:
            gen = CodeGenerator()
            gen.generate(tokens)

            print("=" * 50)
            print("TAC INSTRUCTIONS:")
            for i, ins in enumerate(gen.tac):
                print(f"  {i}: {ins}")
            print("=" * 50)

            result['tacCode'] = "\n".join(str(i) for i in gen.tac)

            interp = TACInterpreter()
            _, events = interp.run(gen.tac, user_inputs=[])

            print("EVENTS:")
            for e in events:
                print(f"  {e}")
            print("=" * 50)

            result['programEvents'] = events
            output_lines.append('✓ Code generation passed')

        except Exception as e:
            import traceback; traceback.print_exc()
            result.update(success=False, errors=[f"Code gen error: {e}"],
                          output='\n'.join(output_lines + ['✗ Code generation failed']),
                          activeAnalysis='codegen')
            return jsonify(result)

        result.update(output='\n'.join(output_lines), activeAnalysis='codegen', success=True)
        return jsonify(result)

    except Exception as e:
        import traceback; print(traceback.format_exc())
        return jsonify({'success': False, 'errors': [f'Server error: {str(e)}'],
                        'syntaxErrors': [], 'semanticErrors': [], 'tokens': [],
                        'syntaxTree': None, 'semanticInfo': None,
                        'activeAnalysis': None, 'tacCode': None,
                        'programEvents': []}), 500


@app.route('/run', methods=['POST'])
def run_with_inputs():
    try:
        data        = request.json
        code        = data.get('code', '')
        user_inputs = data.get('userInputs', [])

        lexer = Lexer()
        tokens, _ = lexer.lexeme(code)

        gen = CodeGenerator()
        gen.generate(tokens)

        print("=" * 50)
        print("TAC INSTRUCTIONS (/run):")
        for i, ins in enumerate(gen.tac):
            print(f"  {i}: {ins}")
        print("=" * 50)

        interp = TACInterpreter()
        _, events = interp.run(gen.tac, user_inputs=user_inputs)

        print("EVENTS (/run):")
        for e in events:
            print(f"  {e}")
        print("=" * 50)

        return jsonify({'success': True, 'events': events})

    except Exception as e:
        import traceback; print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e), 'events': []})


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'phases': ['lexical', 'syntax', 'semantic', 'codegen']})


if __name__ == '__main__':
    print("=" * 60)
    print("CELERITY COMPILER SERVER")
    print("=" * 60)
    print("Server starting on http://localhost:5000")
    print("Phases: Lexical → Syntax → Semantic → Code Gen + TAC Interpreter")
    print("=" * 60)
    app.run(debug=True, port=5000)