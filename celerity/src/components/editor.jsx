import React from 'react';

const Editor = ({ code, setCode, onRun, onStop, isRunning }) => {
  const lineCount = code.split('\n').length;
  const [scrollTop, setScrollTop] = React.useState(0);
  const [scrollLeft, setScrollLeft] = React.useState(0);
  
  // Handle scroll synchronization
  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
    setScrollLeft(e.target.scrollLeft);
  };
  
  // Handle Tab key press
  const handleKeyDown = (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = e.target.selectionStart;
      const end = e.target.selectionEnd;
      const newCode = code.substring(0, start) + '\t' + code.substring(end);
      setCode(newCode);
      
      // Set cursor position after the inserted tab
      setTimeout(() => {
        e.target.selectionStart = e.target.selectionEnd = start + 1;
      }, 0);
    }
  };
  
  // Syntax highlighting
  const highlightCode = (text) => {
    const lines = text.split('\n');
    return lines.map((line, lineIndex) => {
      // Check if line is a comment (starts with #)
      if (line.trim().startsWith('#')) {
        return (
          <div key={lineIndex} style={{ lineHeight: '30px', height: '30px' }}>
            <span style={{ color: '#6A9955', fontStyle: 'italic' }}>{line}</span>
          </div>
        );
      }
      
      // Highlight keywords, datatypes, strings, and numbers
      const keywords = ['if', 'else', 'elseif', 'for', 'while', 'do', 'function', 'return', 'main', 'vacant', 'const', 'struct', 'match', 'pick', 'def', 'split', 'in', 'out', 'is', 'isnot', 'true', 'false'];
      const datatypes = ['num', 'deci', 'word', 'single', 'bool'];
      
      const parts = [];
      const stringRegex = /("[^"]*"|'[^']*')/g;
      const stringMatches = [];
      let stringMatch;
      
      while ((stringMatch = stringRegex.exec(line)) !== null) {
        stringMatches.push({
          start: stringMatch.index,
          end: stringMatch.index + stringMatch[0].length,
          text: stringMatch[0]
        });
      }
      
      let currentPos = 0;
      
      for (let i = 0; i < line.length; i++) {
        const stringAtPos = stringMatches.find(m => m.start === i);
        if (stringAtPos) {
          if (i > currentPos) {
            const beforeText = line.substring(currentPos, i);
            parts.push(highlightNonString(beforeText, keywords, datatypes));
          }
          parts.push(`<span style="color: #CE9178;">${stringAtPos.text}</span>`);
          i = stringAtPos.end - 1;
          currentPos = stringAtPos.end;
        }
      }
      
      if (currentPos < line.length) {
        const remainingText = line.substring(currentPos);
        parts.push(highlightNonString(remainingText, keywords, datatypes));
      }
      
      return (
        <div key={lineIndex} style={{ lineHeight: '30px', height: '30px' }} 
          dangerouslySetInnerHTML={{ __html: parts.join('') || '&nbsp;' }} />
      );
    });
  };
  
  const highlightNonString = (text, keywords, datatypes) => {
    const parts = [];
    let currentPos = 0;
    
    const keywordPattern = `\\b(${keywords.join('|')})\\b`;
    const datatypePattern = `\\b(${datatypes.join('|')})\\b`;
    const numberPattern = `\\b\\d+(\\.\\d+)?\\b`;
    const combinedRegex = new RegExp(`(${keywordPattern}|${datatypePattern}|${numberPattern})`, 'g');
    
    let match;
    while ((match = combinedRegex.exec(text)) !== null) {
      if (match.index > currentPos) {
        parts.push(text.substring(currentPos, match.index));
      }
      
      const word = match[0];
      if (keywords.includes(word)) {
        parts.push(`<span style="color: #FF2222; font-weight: bold;">${word}</span>`);
      } else if (datatypes.includes(word)) {
        parts.push(`<span style="color: #007960;">${word}</span>`);
      } else if (/^\d+(\.\d+)?$/.test(word)) {
        parts.push(`<span style="color: #202000;">${word}</span>`);
      }
      
      currentPos = match.index + word.length;
    }
    
    if (currentPos < text.length) {
      parts.push(text.substring(currentPos));
    }
    
    return parts.join('');
  };

  return (
    <div className="flex-1 flex flex-col">
      {/* Editor Header */}
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-[#333] font-bold text-lg">Code Editor</h2>
        <div className="flex gap-2">
          <button
            onClick={onStop}
            disabled={!isRunning}
            className={`px-6 py-2 rounded font-bold transition-colors ${
              isRunning 
                ? 'bg-[#DC3545] text-white border-2 border-[#B02A37] hover:bg-[#C82333]'
                : 'bg-gray-400 text-gray-200 border-2 border-gray-500 cursor-not-allowed'
            }`}
          >
            ⬛ Stop
          </button>
          <button
            onClick={() => onRun('all')}
            disabled={isRunning}
            className={`px-6 py-2 rounded font-bold transition-colors ${
              isRunning
                ? 'bg-gray-400 text-gray-200 border-2 border-gray-500 cursor-not-allowed'
                : 'bg-[#28A745] text-white border-2 border-[#1E7E34] hover:bg-[#218838]'
            }`}
          >
            ▶ Run
          </button>
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex-1 bg-[#E8DCC8] border-2 border-[#8B7355] overflow-hidden flex relative">
        {/* Line Numbers */}
        <div className="bg-[#D4C4B0] px-2 py-2 text-center text-[#666] select-none overflow-hidden" style={{ 
          fontFamily: 'Consolas, monospace',
          fontSize: '21px',
          minWidth: '55px',
          maxWidth: '55px'
        }}>
          <div style={{ transform: `translateY(-${scrollTop}px)` }}>
            {Array.from({ length: lineCount }, (_, i) => (
              <div key={i} style={{ lineHeight: '30px', height: '30px' }}>
                {i + 1}
              </div>
            ))}
          </div>
        </div>
        
        {/* Highlighted Code Display (Read-only overlay) */}
        <div 
          className="absolute left-0 top-0 p-2 pointer-events-none overflow-hidden"
          style={{ 
            fontFamily: 'Consolas, monospace',
            fontSize: '21px',
            marginLeft: '55px',
            color: '#333',
            lineHeight: '30px',
            tabSize: 2,
            MozTabSize: 2,
            whiteSpace: 'pre',
            padding: '8px',
            width: 'calc(100% - 55px)',
            height: '100%'
          }}
        >
          <div style={{ 
            transform: `translate(-${scrollLeft}px, -${scrollTop}px)`,
            width: 'max-content'
          }}>
            {highlightCode(code)}
          </div>
        </div>
        
        {/* Text Area (Transparent text for input) */}
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          onKeyDown={handleKeyDown}
          onScroll={handleScroll}
          className="flex-1 p-2 bg-transparent resize-none focus:outline-none relative z-10"
          spellCheck="false"
          style={{ 
            tabSize: 2,
            MozTabSize: 2,
            fontFamily: 'Consolas, monospace',
            fontSize: '21px',
            lineHeight: '30px',
            color: 'transparent',
            caretColor: '#333',
            whiteSpace: 'pre',
            overflow: 'auto'
          }}
        />
      </div>
    </div>
  );
};

export default Editor;