import React from 'react';
import ReactMarkdown from 'react-markdown';

interface ReportProps {
  report: any;
  evaluation: any;
}

const ReportViewer: React.FC<ReportProps> = ({ report, evaluation }) => {
  if (!report) return null;

  return (
    <div className="w-full max-w-4xl mx-auto mt-8 space-y-6">
      <div className="bg-white shadow-lg rounded-lg p-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">{report.title}</h1>
        
        {report.sections.map((section: any, idx: number) => (
          <div key={idx} className="mb-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-2">{section.heading}</h3>
            <div className="prose max-w-none text-gray-600">
              {Array.isArray(section.content) ? (
                <ul className="list-disc pl-5">
                    {section.content.map((item: string, i: number) => <li key={i}>{item}</li>)}
                </ul>
              ) : (
                <ReactMarkdown>{section.content}</ReactMarkdown>
              )}
            </div>
          </div>
        ))}
        
        <div className="mt-4 text-sm text-gray-500">
            Agents Involved: {report.metadata.agents_involved.join(', ')}
        </div>
      </div>

      {evaluation && (
        <div className="bg-white shadow-lg rounded-lg p-6">
           <h2 className="text-xl font-bold text-gray-900 mb-4">Evaluation Metrics</h2>
           <div className="grid grid-cols-3 gap-4">
               <div className="bg-blue-50 p-4 rounded text-center">
                   <div className="text-2xl font-bold text-blue-600">{evaluation.metrics.latency_seconds.toFixed(2)}s</div>
                   <div className="text-sm text-gray-600">Latency</div>
               </div>
               <div className="bg-green-50 p-4 rounded text-center">
                   <div className="text-2xl font-bold text-green-600">{(evaluation.metrics.accuracy_score * 100).toFixed(1)}%</div>
                   <div className="text-sm text-gray-600">Accuracy</div>
               </div>
               <div className="bg-purple-50 p-4 rounded text-center">
                   <div className="text-2xl font-bold text-purple-600">{(evaluation.metrics.relevance_score * 100).toFixed(1)}%</div>
                   <div className="text-sm text-gray-600">Relevance</div>
               </div>
           </div>
        </div>
      )}
    </div>
  );
};

export default ReportViewer;
