import React, { useState } from 'react';
import Header from './components/header';
import Editor from './components/editor';
import SidePanel from './components/sidepanel';
import Terminal from './components/terminal';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function App() {
  const [code, setCode] = useState(`main(){\n  #Welcome To Celerity Compiler!\n} \n`);
  const [activeTab, setActiveTab]       = useState('terminal');
  const [output, setOutput]             = useState('');
  const [errors, setErrors]             = useState([]);
  const [tokens, setTokens]             = useState([]);
  const [syntaxErrors, setSyntaxErrors] = useState([]);
  const [syntaxTree, setSyntaxTree]     = useState(null);
  const [semanticErrors, setSemanticErrors] = useState([]);
  const [semanticInfo, setSemanticInfo] = useState(null);
  const [activeAnalysis, setActiveAnalysis] = useState(null);
  const [tacCode, setTacCode]           = useState(null);
  const [programEvents, setProgramEvents] = useState([]);

  const handleTabSwitch = (tabName) => setActiveAnalysis(tabName);

  const handleRun = async (analysisType) => {
    setActiveTab('terminal');
    setErrors([]);
    setTokens([]);
    setSyntaxErrors([]);
    setSyntaxTree(null);
    setSemanticErrors([]);
    setSemanticInfo(null);
    setTacCode(null);
    setProgramEvents([]);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, analysisType })
      });

      const data = await response.json();
      console.log('Backend response:', data);

      if (data.success) {
        setActiveAnalysis(data.activeAnalysis);
        if (data.tokens?.length)     setTokens(data.tokens);
        if (data.syntaxTree)         setSyntaxTree(data.syntaxTree);
        if (data.semanticInfo)       setSemanticInfo(data.semanticInfo);
        if (data.tacCode)            setTacCode(data.tacCode);
        if (data.programEvents?.length) {
          setProgramEvents(data.programEvents);
          setActiveTab('generate');
        }

        let outputMessages = [''];
        data.output.split('\n').forEach(line => {
          if (line.includes('✓'))
            outputMessages.push(`<span style="color: green;">${line}</span><br>`);
          else if (line.includes('✗') || line.includes('X'))
            outputMessages.push(`<span style="color: red;">${line}</span><br>`);
          else
            outputMessages.push(`${line}<br>`);
        });
        setOutput(outputMessages.join(''));
        if (data.errors?.length)          setErrors(data.errors);
        if (data.syntaxErrors?.length)    setSyntaxErrors(data.syntaxErrors);
        if (data.semanticErrors?.length)  setSemanticErrors(data.semanticErrors);

      } else {
        let outputMessages = ['<b>Running code...</b><br>'];
        const phase = data.activeAnalysis;
        if (phase === 'lexical')
          outputMessages.push('<span style="color: red;">X Lexical analysis failed</span><br>');
        else if (phase === 'syntax') {
          outputMessages.push('<span style="color: green;">✓ Lexical analysis passed</span><br>');
          outputMessages.push('<span style="color: red;">X Syntax analysis failed</span><br>');
        } else if (phase === 'semantic') {
          outputMessages.push('<span style="color: green;">✓ Lexical analysis passed</span><br>');
          outputMessages.push('<span style="color: green;">✓ Syntax analysis passed</span><br>');
          outputMessages.push('<span style="color: red;">X Semantic analysis failed</span><br>');
        } else if (phase === 'codegen') {
          outputMessages.push('<span style="color: green;">✓ Lexical analysis passed</span><br>');
          outputMessages.push('<span style="color: green;">✓ Syntax analysis passed</span><br>');
          outputMessages.push('<span style="color: green;">✓ Semantic analysis passed</span><br>');
          outputMessages.push('<span style="color: red;">X Code generation failed</span><br>');
        }
        setOutput(outputMessages.join(''));
        setErrors(data.errors || ['Analysis failed']);
        setActiveAnalysis(phase);
        if (data.tokens?.length)        setTokens(data.tokens);
        if (data.syntaxTree)            setSyntaxTree(data.syntaxTree);
        if (data.syntaxErrors?.length)  setSyntaxErrors(data.syntaxErrors);
        if (data.semanticErrors?.length) setSemanticErrors(data.semanticErrors);
      }
    } catch (error) {
      setErrors([`Connection error: ${error.message}`]);
      setOutput('<span style="color: red;">Failed to connect to backend. Make sure Flask server is running on port 5000.</span>');
      setActiveAnalysis(null);
    }
  };

  const handleStop = () => {
    setOutput('');
    setErrors([]);
    setTokens([]);
    setSyntaxErrors([]);
    setSyntaxTree(null);
    setSemanticErrors([]);
    setSemanticInfo(null);
    setActiveAnalysis(null);
    setTacCode(null);
    setProgramEvents([]);
  };

  return (
    <div className="w-screen h-screen flex flex-col bg-[#DFC7A8] overflow-hidden">
      <Header />
      <div className="flex-1 flex flex-col p-4 gap-2 min-h-0">
        <div className="flex-1 flex gap-3 min-h-0">
          <Editor code={code} setCode={setCode} onRun={handleRun} onStop={handleStop} />
          <SidePanel
            tokens={tokens}
            activeAnalysis={activeAnalysis}
            syntaxErrors={syntaxErrors}
            syntaxTree={syntaxTree}
            semanticErrors={semanticErrors}
            semanticInfo={semanticInfo}
            onAnalysisClick={handleRun}
            onTabSwitch={handleTabSwitch}
          />
        </div>
        <Terminal
          output={output}
          errors={errors}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          tacCode={tacCode}
          programEvents={programEvents}
          sourceCode={code}
        />
      </div>
    </div>
  );
}

export default App;
