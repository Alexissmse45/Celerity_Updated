import React from 'react';

const SidePanel = ({ tokens, activeAnalysis, syntaxTree, semanticInfo, syntaxErrors, semanticErrors, onTabSwitch }) => {
  return (
    <div className="w-96 bg-[#e8dcc8] border-2 border-[#8B7355] flex flex-col">
      {/* Analysis Header with Tabs */}
      <div className="bg-[#d4c4a8] border-b-2 border-[#8B7355]">
        <div className="flex">
          <button
            onClick={() => onTabSwitch && onTabSwitch('lexical')}
            className={`flex-1 px-4 py-2 font-semibold transition-colors ${
              activeAnalysis === 'lexical'
                ? 'bg-[#e8dcc8] text-gray-800 border-b-2 border-[#8B7355]'
                : 'bg-[#c4b5a0] text-gray-600 hover:bg-[#d4c4a8]'
            }`}
          >
            Lexical
          </button>
          <button
            onClick={() => onTabSwitch && onTabSwitch('syntax')}
            className={`flex-1 px-4 py-2 font-semibold transition-colors ${
              activeAnalysis === 'syntax'
                ? 'bg-[#e8dcc8] text-gray-800 border-b-2 border-[#8B7355]'
                : 'bg-[#c4b5a0] text-gray-600 hover:bg-[#d4c4a8]'
            }`}
          >
            Syntax
          </button>
          <button
            onClick={() => onTabSwitch && onTabSwitch('semantic')}
            className={`flex-1 px-4 py-2 font-semibold transition-colors ${
              activeAnalysis === 'semantic'
                ? 'bg-[#e8dcc8] text-gray-800 border-b-2 border-[#8B7355]'
                : 'bg-[#c4b5a0] text-gray-600 hover:bg-[#d4c4a8]'
            }`}
          >
            Semantic
          </button>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto">
        {/* LEXICAL ANALYSIS - Token Table */}
        {activeAnalysis === 'lexical' && (
          <div className="h-full">
            {tokens && tokens.length > 0 ? (
              <table className="w-full text-sm border-collapse">
                <thead className="sticky top-0 bg-[#c4a57b]">
                  <tr>
                    <th className="border border-[#8B7355] px-2 py-2 text-left font-semibold">#</th>
                    <th className="border border-[#8B7355] px-2 py-2 text-left font-semibold">Lexeme</th>
                    <th className="border border-[#8B7355] px-2 py-2 text-left font-semibold">Token</th>
                    <th className="border border-[#8B7355] px-2 py-2 text-left font-semibold">Line</th>
                    <th className="border border-[#8B7355] px-2 py-2 text-left font-semibold">Column</th>
                  </tr>
                </thead>
                <tbody>
                  {tokens.map((token, index) => (
                    <tr key={index} className="hover:bg-[#d4c4a8]">
                      <td className="border border-[#8B7355] px-2 py-1 text-gray-700">{index + 1}</td>
                      <td className="border border-[#8B7355] px-2 py-1 text-gray-700 font-mono">{token.lexeme}</td>
                      <td className="border border-[#8B7355] px-2 py-1 text-gray-700">{token.token}</td>
                      <td className="border border-[#8B7355] px-2 py-1 text-gray-700">{token.line}</td>
                      <td className="border border-[#8B7355] px-2 py-1 text-gray-700">{token.column}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="flex items-center justify-center h-full p-4">
                <div className="text-center text-gray-600">
                  <p className="font-semibold mb-2">No Tokens</p>
                  <p className="text-sm">Run lexical analysis to see tokens</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* SYNTAX ANALYSIS - Clean Display */}
        {activeAnalysis === 'syntax' && (
          <div className="h-full">
            {syntaxErrors && syntaxErrors.length > 0 ? (
              // Show Errors
              <div className="p-4">
                <div className="text-gray-700">
                  <p className="font-semibold mb-3 text-red-600">Syntax Errors:</p>
                  <div className="bg-white p-3 rounded border border-red-400 max-h-96 overflow-auto">
                    {syntaxErrors.map((error, index) => (
                      <div key={index} className="text-red-600 mb-2 text-sm">
                        {error}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : syntaxTree ? (
              // Show Success Message
              <div className="flex items-center justify-center h-full p-4">
                <div className="text-center text-green-600">
                  <div className="text-5xl mb-3">✓</div>
                  <p className="font-semibold text-lg mb-2">Syntax Analysis Completed</p>
                  <p className="text-sm text-gray-600">No errors found</p>
                </div>
              </div>
            ) : (
              // No Analysis Yet
              <div className="flex items-center justify-center h-full p-4">
                <div className="text-center text-gray-600">
                  <p className="font-semibold mb-2">Syntax Analysis</p>
                  <p className="text-sm">Run syntax analysis to see results</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* SEMANTIC ANALYSIS - Symbol Table and Errors */}
        {activeAnalysis === 'semantic' && (
          <div className="h-full">
            {semanticErrors && semanticErrors.length > 0 ? (
              // Show Semantic Errors
              <div className="p-4">
                <div className="text-gray-700">
                  <p className="font-semibold mb-3 text-red-600">Semantic Errors:</p>
                  <div className="bg-white p-3 rounded border border-red-400 max-h-96 overflow-auto">
                    {semanticErrors.map((error, index) => (
                      <div key={index} className="text-red-600 mb-2 text-sm font-mono">
                        {error}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : semanticInfo ? (
              // Show Symbol Table
              <div className="p-4">
                <div className="text-gray-700">
                  <p className="font-semibold mb-3 text-green-600">✓ Semantic Analysis Passed</p>
                  
                  {/* Symbol Table */}
                  {semanticInfo.symbol_table && Object.keys(semanticInfo.symbol_table).length > 0 && (
                    <div className="mb-4">
                      <p className="font-semibold mb-2 text-gray-800">Symbol Table:</p>
                      <div className="bg-white p-3 rounded border border-gray-300 max-h-80 overflow-auto">
                        {Object.entries(semanticInfo.symbol_table).map(([scope, symbols]) => (
                          <div key={scope} className="mb-4">
                            <p className="font-semibold text-sm mb-2 text-blue-600">Scope: {scope}</p>
                            <table className="w-full text-xs border-collapse">
                              <thead className="bg-gray-100">
                                <tr>
                                  <th className="border border-gray-300 px-2 py-1 text-left">Name</th>
                                  <th className="border border-gray-300 px-2 py-1 text-left">Type</th>
                                  <th className="border border-gray-300 px-2 py-1 text-left">Data Type</th>
                                  <th className="border border-gray-300 px-2 py-1 text-left">Line</th>
                                </tr>
                              </thead>
                              <tbody>
                                {Object.entries(symbols).map(([name, symbol]) => (
                                  <tr key={name} className="hover:bg-gray-50">
                                    <td className="border border-gray-300 px-2 py-1 font-mono">{name}</td>
                                    <td className="border border-gray-300 px-2 py-1">{symbol.symbol_type}</td>
                                    <td className="border border-gray-300 px-2 py-1">{symbol.data_type || '-'}</td>
                                    <td className="border border-gray-300 px-2 py-1">{symbol.line}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Struct Table */}
                  {semanticInfo.struct_table && Object.keys(semanticInfo.struct_table).length > 0 && (
                    <div className="mb-4">
                      <p className="font-semibold mb-2 text-gray-800">Struct Definitions:</p>
                      <div className="bg-white p-3 rounded border border-gray-300 max-h-60 overflow-auto">
                        {Object.entries(semanticInfo.struct_table).map(([structName, fields]) => (
                          <div key={structName} className="mb-3">
                            <p className="font-semibold text-sm mb-1 text-purple-600">struct {structName}</p>
                            <table className="w-full text-xs border-collapse ml-4">
                              <thead className="bg-gray-100">
                                <tr>
                                  <th className="border border-gray-300 px-2 py-1 text-left">Field</th>
                                  <th className="border border-gray-300 px-2 py-1 text-left">Type</th>
                                </tr>
                              </thead>
                              <tbody>
                                {fields.map((field, idx) => (
                                  <tr key={idx} className="hover:bg-gray-50">
                                    <td className="border border-gray-300 px-2 py-1 font-mono">{field[0]}</td>
                                    <td className="border border-gray-300 px-2 py-1">{field[1]}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              // No Analysis Yet
              <div className="flex items-center justify-center h-full p-4">
                <div className="text-center text-gray-600">
                  <p className="font-semibold mb-2">Semantic Analysis</p>
                  <p className="text-sm">Run semantic analysis to see results</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* DEFAULT - No Analysis Selected */}
        {!activeAnalysis && (
          <div className="flex items-center justify-center h-full p-4">
            <div className="text-center text-gray-600 text-sm">
              <p>Click Run to start analysis</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SidePanel;