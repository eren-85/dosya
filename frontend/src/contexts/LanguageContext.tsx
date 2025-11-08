/**
 * Language Context
 * Manages app language state (Turkish/English)
 */

import { createContext, useContext, useState, ReactNode, useEffect } from 'react';
import { Language, Translations, getTranslations, getSavedLanguage, saveLanguage } from '@/lib/i18n';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(getSavedLanguage());
  const [t, setT] = useState<Translations>(getTranslations(language));

  useEffect(() => {
    // Update translations when language changes
    setT(getTranslations(language));
  }, [language]);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    saveLanguage(lang);
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

// Custom hook to use language context
export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
