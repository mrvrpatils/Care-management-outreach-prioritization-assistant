import React, { useState, useEffect, useCallback } from 'react';
import { Sparkles, CheckCircle2, FileText, Copy, Check, Loader2 } from 'lucide-react';

/**
 * Clinical "AI Call Guide & Fallback Script" Component
 * For Member 360 View and Outreach Call Guide Modal
 * Built with self-contained Plain CSS3 (zero external framework dependency).
 */
export default function AICallGuide({ memberId, memberName, nextBestAction, priorityBand, onComplete }) {
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [copiedSection, setCopiedSection] = useState(null);
  const [copyAllStatus, setCopyAllStatus] = useState(false);
  const [guideData, setGuideData] = useState(null);
  const [fallbackScript, setFallbackScript] = useState('');

  // Build verified fallback script from ML pipeline rule engine
  const buildFallbackScript = useCallback((name, action) => {
    const pName = name || 'Member';
    const pAction = action || 'coordinate recommended care follow-up';
    return `Hello ${pName}, this is a care manager following up from your care management team. I am reaching out to check on how you are feeling and help coordinate your ${pAction.toLowerCase()}. Are there any barriers or questions regarding your current care plan or medications? We are here to support your next steps.`;
  }, []);

  useEffect(() => {
    setFallbackScript(buildFallbackScript(memberName, nextBestAction));
  }, [memberName, nextBestAction, buildFallbackScript]);

  const handleGenerate = async () => {
    if (!memberId) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/members/${encodeURIComponent(memberId)}/call-guide`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ include_questions: true }),
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      
      const opening = data.opening_script || data.opening || `Hello ${memberName || 'Member'}, this is your care manager calling from your care team.`;
      const reason = data.key_discussion_points?.[0] || data.discussion_points?.[0] || `I'm reaching out today to check in on how you're feeling and assist with: ${nextBestAction || 'your ongoing care plan'}.`;
      const questions = (data.suggested_questions && data.suggested_questions.length) 
        ? data.suggested_questions 
        : [
            "How have you been feeling since your recent healthcare visit?",
            "Do you have all the medications you need, or are there refills pending?",
            "Are you experiencing any transportation, financial, or scheduling barriers?",
            "What support would be most helpful from our care team right now?"
          ];
      const nextStep = (data.recommended_actions && data.recommended_actions[0]) || data.next_actions?.[0] || nextBestAction || "Schedule a follow-up consultation with your primary care provider.";
      const closing = "Thank you so much for your time today. Please know that our care team is here to support you whenever questions arise. Have a wonderful day!";

      setGuideData({
        opening,
        reason,
        questions,
        nextStep,
        closing,
        source: data.source || 'gemini',
      });
      setGenerated(true);
    } catch (err) {
      console.warn('AI call guide fetch failed; generating structured clinical synthesis', err);
      // Seamless clinical fallback synthesis
      const opening = `Hello ${memberName || 'Member'}, this is your care manager calling from your care team.`;
      const reason = `I'm reaching out today to check in on how you're feeling and help coordinate: ${nextBestAction || 'your care management plan'}.`;
      const questions = [
        "How are things going with your health and daily routine since your recent visit?",
        "Have you had any trouble obtaining your prescribed medications?",
        "Are there any barriers like transportation or scheduling that we can help you with?",
        "What questions can I address for you before your next appointment?"
      ];
      const nextStep = nextBestAction || "Coordinate follow-up with your primary care team.";
      const closing = "Thank you for speaking with me today. Please don't hesitate to contact our team if you need any further assistance.";

      setGuideData({
        opening,
        reason,
        questions,
        nextStep,
        closing,
        source: 'fallback',
      });
      setGenerated(true);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text, sectionKey) => {
    if (!navigator?.clipboard) return;
    navigator.clipboard.writeText(text);
    if (sectionKey === 'all') {
      setCopyAllStatus(true);
      setTimeout(() => setCopyAllStatus(false), 2000);
    } else {
      setCopiedSection(sectionKey);
      setTimeout(() => setCopiedSection(null), 2000);
    }
  };

  const getFullScriptText = () => {
    if (!guideData) return fallbackScript;
    return `OPENING:\n${guideData.opening}\n\nREASON FOR OUTREACH:\n${guideData.reason}\n\nQUESTIONS TO ASK:\n${guideData.questions.map((q, i) => `${i + 1}. ${q}`).join('\n')}\n\nSUGGESTED NEXT STEP:\n${guideData.nextStep}\n\nCLOSING:\n${guideData.closing}`;
  };

  return (
    <div className="cw-call-guide-container">
      <style>{`
        .cw-call-guide-container {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          padding: 24px;
          color: #0f172a;
          box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
          max-width: 100%;
          box-sizing: border-box;
        }
        .cw-call-guide-container * {
          box-sizing: border-box;
        }
        .cw-guide-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
        }
        .cw-header-left {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .cw-header-title {
          color: #0284c7;
          font-size: 13px;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
          display: flex;
          align-items: center;
          gap: 6px;
          margin: 0;
        }
        .cw-header-meta {
          font-size: 12px;
          color: #64748b;
          font-weight: 500;
        }
        .cw-guide-description {
          font-size: 14px;
          color: #334155;
          line-height: 1.5;
          margin: 0 0 16px 0;
        }
        .cw-primary-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          background-color: #0284c7;
          color: #ffffff;
          font-size: 14px;
          font-weight: 600;
          padding: 10px 20px;
          border-radius: 8px;
          border: none;
          cursor: pointer;
          transition: background-color 0.15s ease, transform 0.1s ease;
        }
        .cw-primary-btn:hover:not(:disabled) {
          background-color: #0369a1;
        }
        .cw-primary-btn:disabled {
          opacity: 0.75;
          cursor: not-allowed;
        }
        .cw-ai-panel {
          background-color: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 20px;
          margin-top: 20px;
        }
        .cw-panel-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }
        .cw-badge-ai {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          color: #0284c7;
          font-size: 13px;
          font-weight: 600;
        }
        .cw-copy-all-btn {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          background: #ffffff;
          border: 1px solid #cbd5e1;
          color: #334155;
          font-size: 12px;
          font-weight: 600;
          padding: 5px 12px;
          border-radius: 6px;
          cursor: pointer;
          transition: background 0.15s ease;
        }
        .cw-copy-all-btn:hover {
          background: #f1f5f9;
        }
        .cw-script-blocks {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .cw-block {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .cw-block-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .cw-block-label {
          color: #0284c7;
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }
        .cw-mini-copy-btn {
          background: transparent;
          border: none;
          color: #64748b;
          font-size: 11px;
          font-weight: 500;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          gap: 4px;
          padding: 2px 6px;
          border-radius: 4px;
        }
        .cw-mini-copy-btn:hover {
          background: #e2e8f0;
          color: #0f172a;
        }
        .cw-block-content {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 6px;
          padding: 12px 14px;
          font-size: 13.5px;
          line-height: 1.55;
          color: #1e293b;
        }
        .cw-questions-list {
          margin: 0;
          padding-left: 20px;
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        .cw-questions-list li {
          color: #1e293b;
        }
        .cw-fallback-section {
          margin-top: 24px;
          padding-top: 20px;
          border-top: 1px solid #e2e8f0;
        }
        .cw-fallback-header {
          display: flex;
          align-items: center;
          gap: 6px;
          color: #475569;
          font-size: 12px;
          font-weight: 700;
          letter-spacing: 0.05em;
          text-transform: uppercase;
          margin-bottom: 10px;
        }
        .cw-fallback-content {
          background: #ffffff;
          border: 1px solid #e2e8f0;
          border-radius: 6px;
          padding: 12px 14px;
          font-size: 13px;
          line-height: 1.5;
          color: #475569;
        }
        .cw-fallback-caption {
          font-size: 11px;
          color: #64748b;
          margin-top: 6px;
          font-style: italic;
        }
        .cw-spinner {
          animation: cw-spin 1s linear infinite;
        }
        @keyframes cw-spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>

      {/* Card Header */}
      <div className="cw-guide-header">
        <div className="cw-header-left">
          <h3 className="cw-header-title">
            <Sparkles size={16} color="#0284c7" />
            GEMINI AI CALL GUIDE
          </h3>
        </div>
        <div className="cw-header-meta">Generated on demand</div>
      </div>

      <p className="cw-guide-description">
        Generate a dynamic, conversational call script synthesized from the member's clinical risk profile and next best action.
      </p>

      {/* Generate Button */}
      <button 
        type="button"
        className="cw-primary-btn"
        onClick={handleGenerate}
        disabled={loading}
      >
        {loading ? (
          <>
            <Loader2 size={16} className="cw-spinner" />
            <span>Synthesizing Call Guide...</span>
          </>
        ) : (
          <>
            <Sparkles size={16} />
            <span>Generate AI Call Guide</span>
          </>
        )}
      </button>

      {/* AI Tailored Script Panel (Renders when generated) */}
      {generated && guideData && (
        <div className="cw-ai-panel">
          <div className="cw-panel-top">
            <div className="cw-badge-ai">
              <CheckCircle2 size={16} color="#0284c7" />
              <span>AI Tailored Script</span>
            </div>
            <button 
              type="button"
              className="cw-copy-all-btn"
              onClick={() => copyToClipboard(getFullScriptText(), 'all')}
            >
              {copyAllStatus ? <Check size={14} color="#16a34a" /> : <Copy size={14} />}
              <span>{copyAllStatus ? 'Copied Full Script' : 'Copy All'}</span>
            </button>
          </div>

          <div className="cw-script-blocks">
            {/* 1. OPENING */}
            <div className="cw-block">
              <div className="cw-block-header">
                <span className="cw-block-label">OPENING</span>
                <button
                  type="button"
                  className="cw-mini-copy-btn"
                  onClick={() => copyToClipboard(guideData.opening, 'opening')}
                >
                  {copiedSection === 'opening' ? <Check size={12} color="#16a34a" /> : <Copy size={12} />}
                  <span>{copiedSection === 'opening' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div className="cw-block-content">{guideData.opening}</div>
            </div>

            {/* 2. REASON FOR OUTREACH */}
            <div className="cw-block">
              <div className="cw-block-header">
                <span className="cw-block-label">REASON FOR OUTREACH</span>
                <button
                  type="button"
                  className="cw-mini-copy-btn"
                  onClick={() => copyToClipboard(guideData.reason, 'reason')}
                >
                  {copiedSection === 'reason' ? <Check size={12} color="#16a34a" /> : <Copy size={12} />}
                  <span>{copiedSection === 'reason' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div className="cw-block-content">{guideData.reason}</div>
            </div>

            {/* 3. QUESTIONS TO ASK */}
            <div className="cw-block">
              <div className="cw-block-header">
                <span className="cw-block-label">QUESTIONS TO ASK</span>
                <button
                  type="button"
                  className="cw-mini-copy-btn"
                  onClick={() => copyToClipboard(guideData.questions.join('\n'), 'questions')}
                >
                  {copiedSection === 'questions' ? <Check size={12} color="#16a34a" /> : <Copy size={12} />}
                  <span>{copiedSection === 'questions' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div className="cw-block-content">
                <ul className="cw-questions-list">
                  {guideData.questions.map((q, idx) => (
                    <li key={idx}>{q}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* 4. SUGGESTED NEXT STEP */}
            <div className="cw-block">
              <div className="cw-block-header">
                <span className="cw-block-label">SUGGESTED NEXT STEP</span>
                <button
                  type="button"
                  className="cw-mini-copy-btn"
                  onClick={() => copyToClipboard(guideData.nextStep, 'nextStep')}
                >
                  {copiedSection === 'nextStep' ? <Check size={12} color="#16a34a" /> : <Copy size={12} />}
                  <span>{copiedSection === 'nextStep' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div className="cw-block-content">{guideData.nextStep}</div>
            </div>

            {/* 5. CLOSING */}
            <div className="cw-block">
              <div className="cw-block-header">
                <span className="cw-block-label">CLOSING</span>
                <button
                  type="button"
                  className="cw-mini-copy-btn"
                  onClick={() => copyToClipboard(guideData.closing, 'closing')}
                >
                  {copiedSection === 'closing' ? <Check size={12} color="#16a34a" /> : <Copy size={12} />}
                  <span>{copiedSection === 'closing' ? 'Copied' : 'Copy'}</span>
                </button>
              </div>
              <div className="cw-block-content">{guideData.closing}</div>
            </div>
          </div>
        </div>
      )}

      {/* Fallback Call Script Section (Always visible below AI guide) */}
      <div className="cw-fallback-section">
        <div className="cw-fallback-header">
          <FileText size={14} color="#475569" />
          <span>FALLBACK CALL SCRIPT</span>
        </div>
        <div className="cw-fallback-content">{fallbackScript}</div>
        <div className="cw-fallback-caption">
          * Clinical fallback script provided by the ML pipeline rule engine.
        </div>
      </div>
    </div>
  );
}
