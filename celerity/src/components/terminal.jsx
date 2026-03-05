import React, { useState, useEffect, useRef } from 'react';

const Terminal = ({
  output, errors, activeTab, setActiveTab,
  tacCode,
  programEvents,
  sourceCode,
}) => {
  const [events, setEvents]           = useState([]);
  const [inputValues, setInputValues] = useState({});
  const [submitted, setSubmitted]     = useState(false);
  const [running, setRunning]         = useState(false);
  const inputRefs                     = useRef({});
  const outputEndRef                  = useRef(null);

  useEffect(() => {
    if (programEvents && programEvents.length > 0) {
      setEvents(programEvents);
      setInputValues({});
      setSubmitted(false);
      setRunning(false);
      setTimeout(() => {
        const first = programEvents.find(e => e.type === 'input_prompt');
        if (first) inputRefs.current[first.inputIndex]?.focus();
      }, 80);
    } else {
      setEvents([]);
      setInputValues({});
      setSubmitted(false);
      setRunning(false);
    }
  }, [programEvents]);

  useEffect(() => {
    outputEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events, running]);

  const inputPrompts = events.filter(e => e.type === 'input_prompt');
  const allFilled    = inputPrompts.length > 0
    && inputPrompts.every(e => (inputValues[e.inputIndex] ?? '').trim() !== '');

  const handleChange = (idx, val) => setInputValues(prev => ({ ...prev, [idx]: val }));

  const handleKeyDown = (e, idx) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    const pos = inputPrompts.findIndex(p => p.inputIndex === idx);
    if (pos < inputPrompts.length - 1) {
      inputRefs.current[inputPrompts[pos + 1].inputIndex]?.focus();
    } else if (allFilled) {
      submitAll();
    }
  };

  const submitAll = async () => {
    if (running || submitted) return;
    setRunning(true);
    const ordered    = [...inputPrompts].sort((a, b) => a.inputIndex - b.inputIndex);
    const userInputs = ordered.map(p => (inputValues[p.inputIndex] ?? '').trim());
    try {
      const res  = await fetch('http://localhost:5000/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: sourceCode, userInputs })
      });
      const data = await res.json();
      if (data.events?.length) {
        setEvents(data.events);
        setSubmitted(true);
      } else {
        setEvents(prev => [...prev,
          { type: 'output', text: data.error ? `[error: ${data.error}]` : '[no output]' }
        ]);
      }
    } catch (err) {
      setEvents(prev => [...prev, { type: 'output', text: `[connection error: ${err.message}]` }]);
    }
    setRunning(false);
  };

  const buildRows = () => {
    const rows = [];
    let i = 0;
    while (i < events.length) {
      const ev = events[i];
      if (ev.type === 'input_prompt') {
        let promptText = ev.text;
        if (!promptText && rows.length > 0 && rows[rows.length - 1].type === 'output') {
          promptText = rows.pop().text;
        }
        rows.push({ type: 'input_prompt', promptText, ev });
        i++;
      } else {
        rows.push({ type: 'output', text: ev.text });
        i++;
      }
    }
    return rows;
  };

  const renderRow = (row, i) => {
    if (row.type === 'output') {
      // Split on \n so out("\n") creates an actual new line
      const lines = row.text.split('\\n');
      return (
        <div key={i}>
          {lines.map((line, j) => (
            <div key={j} style={{ whiteSpace: 'pre', minHeight: '1em' }}>{line}</div>
          ))}
        </div>
      );
    }

    if (row.type === 'input_prompt') {
      const { promptText, ev } = row;
      const idx    = ev.inputIndex;
      const isDone = submitted || (ev.userValue !== '' && ev.userValue != null);
      const value  = isDone
        ? (ev.userValue || inputValues[idx] || '')
        : (inputValues[idx] ?? '');

      return (
        <div key={i} style={{ display: 'flex', alignItems: 'baseline', whiteSpace: 'pre' }}>
          {promptText ? <span>{promptText}</span> : null}
          {isDone ? (
            <span style={{ color: '#8B5E3C', fontWeight: 'bold' }}>{value}</span>
          ) : (
            <input
              ref={el => inputRefs.current[idx] = el}
              type="text"
              value={value}
              onChange={e => handleChange(idx, e.target.value)}
              onKeyDown={e => handleKeyDown(e, idx)}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: '1px solid #8B7355',
                outline: 'none',
                fontFamily: 'Consolas, monospace',
                fontSize: '9pt',
                color: '#8B5E3C',
                minWidth: '60px',
                width: `${Math.max(60, (value.length + 2) * 7.8)}px`,
                padding: 0,
              }}
            />
          )}
        </div>
      );
    }
    return null;
  };

  const TabBtn = ({ id, label }) => (
    <button
      onClick={() => setActiveTab(id)}
      className={`px-5 py-2 border-2 border-[#8B7355] transition-colors ${
        activeTab === id
          ? 'bg-[#E8DCC8] text-[#333] hover:bg-[#D4C4B0] rounded-t'
          : 'bg-[#C8B5A0] text-[#333] border-b-0 rounded-t'
      }`}
    >{label}</button>
  );

  return (
    <div className="flex flex-col" style={{ height: '240px' }}>
      <div className="flex gap-1">
        <TabBtn id="terminal" label="Terminal"       />
        <TabBtn id="generate" label="Generated Code" />
        <TabBtn id="tac"      label="TAC"            />
      </div>

      <div
        className="flex-1 bg-[#E8DCC8] border-2 border-[#8B7355] text-[#333] overflow-hidden flex flex-col"
        style={{ fontFamily: 'Consolas, monospace', fontSize: '9pt' }}
      >
        {activeTab === 'terminal' && (
          <div className="flex-1 overflow-auto p-3">
            {output && <div dangerouslySetInnerHTML={{ __html: output }} />}
            {errors?.length > 0 && (
              <div style={{ marginTop: '12px' }}>
                <div style={{ fontWeight: 'bold', color: '#DC3545', marginBottom: '6px' }}>⚠️ Errors:</div>
                {errors.map((e, i) => (
                  <div key={i} style={{ color: '#DC3545', marginBottom: '4px' }}>{e}</div>
                ))}
              </div>
            )}
            {!output && !errors?.length && (
              <span style={{ color: '#666' }}>Terminal cleared. Click 'Run' to execute.</span>
            )}
          </div>
        )}

        {activeTab === 'generate' && (
          <div className="flex-1 overflow-auto p-3">
            {events.length === 0 && !running && (
              <span style={{ color: '#999' }}>No output yet — run the code first.</span>
            )}
            {buildRows().map((row, i) => renderRow(row, i))}
            {running && <div style={{ color: '#999' }}>Running...</div>}
            {!submitted && !running && allFilled && (
              <div style={{ marginTop: '10px' }}>
                <button onClick={submitAll} style={{
                  padding: '3px 14px', background: '#8B7355', color: '#fff',
                  border: 'none', borderRadius: '3px', cursor: 'pointer',
                  fontSize: '8pt', fontFamily: 'Consolas, monospace',
                }}>▶ Run</button>
                <span style={{ color: '#999', marginLeft: '8px', fontSize: '8pt' }}>
                  or press Enter on the last input
                </span>
              </div>
            )}
            <div ref={outputEndRef} />
          </div>
        )}

        {activeTab === 'tac' && (
          <div className="flex-1 overflow-auto p-3">
            {tacCode ? (
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {tacCode.split('\n').map((line, i) => (
                  <div key={i} style={{ display: 'flex', gap: '12px' }}>
                    <span style={{ color: '#999', userSelect: 'none', minWidth: '32px', textAlign: 'right', flexShrink: 0 }}>
                      {String(i).padStart(3, ' ')}
                    </span>
                    <span>{line}</span>
                  </div>
                ))}
              </pre>
            ) : (
              <span style={{ color: '#999' }}>No TAC yet — run the code first.</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Terminal;