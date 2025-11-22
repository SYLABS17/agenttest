import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { researchAPI } from '../../services/api';

interface QuerySuggestionsProps {
  onSuggestionClick: (suggestion: string) => void;
}

const QuerySuggestions: React.FC<QuerySuggestionsProps> = ({ onSuggestionClick }) => {
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    fetchSuggestions();
  }, []);

  const fetchSuggestions = async () => {
    try {
      const response = await researchAPI.getTestQueries();
      setSuggestions(response.queries.slice(0, 6));
    } catch (error) {
      // Fallback suggestions
      setSuggestions([
        'Future of renewable energy in Africa',
        'Impact of generative AI on journalism',
        'Best practices for cloud-native application development',
        'Quantum computing applications in drug discovery',
        'Sustainable urban planning strategies for 2030',
        'Blockchain adoption in supply chain management',
      ]);
    }
  };

  return (
    <div className="w-full max-w-2xl">
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
        Try one of these research topics:
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {suggestions.map((suggestion, index) => (
          <motion.button
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            onClick={() => onSuggestionClick(suggestion)}
            className="text-left px-4 py-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 hover:border-primary-500 dark:hover:border-primary-400 transition-colors group"
          >
            <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-primary-600 dark:group-hover:text-primary-400">
              {suggestion}
            </span>
          </motion.button>
        ))}
      </div>
    </div>
  );
};

export default QuerySuggestions;