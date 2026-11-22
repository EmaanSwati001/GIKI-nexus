import React, { createContext, useContext, useState, useEffect } from 'react';

export interface SavedItem {
  id: string;
  type: 'course' | 'faculty' | 'project' | 'research';
  title: string;
  subtitle?: string;
  link: string;
  savedAt: string;
}

export interface RecentlyViewedItem {
  id: string;
  type: 'course' | 'faculty' | 'project' | 'program';
  title: string;
  subtitle?: string;
  link: string;
  viewedAt: string;
}

export interface StoredKey {
  entityId: string;
  entityType: 'profile' | 'project';
  title: string;
  key: string;
  createdAt: string;
}

interface SavedContextType {
  savedItems: SavedItem[];
  toggleSave: (item: Omit<SavedItem, 'savedAt'>) => void;
  isSaved: (id: string) => boolean;
  recentlyViewed: RecentlyViewedItem[];
  addRecentlyViewed: (item: Omit<RecentlyViewedItem, 'viewedAt'>) => void;
  storedKeys: StoredKey[];
  saveKey: (keyInfo: StoredKey) => void;
  removeKey: (entityId: string) => void;
}

const SavedContext = createContext<SavedContextType | undefined>(undefined);

export const SavedProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [savedItems, setSavedItems] = useState<SavedItem[]>(() => {
    try {
      const stored = localStorage.getItem('giki_nexus_saved');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const [recentlyViewed, setRecentlyViewed] = useState<RecentlyViewedItem[]>(() => {
    try {
      const stored = localStorage.getItem('giki_nexus_recent');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  const [storedKeys, setStoredKeys] = useState<StoredKey[]>(() => {
    try {
      const stored = localStorage.getItem('giki_nexus_keys');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('giki_nexus_saved', JSON.stringify(savedItems));
    } catch {
      // storage error
    }
  }, [savedItems]);

  useEffect(() => {
    try {
      localStorage.setItem('giki_nexus_recent', JSON.stringify(recentlyViewed));
    } catch {
      // storage error
    }
  }, [recentlyViewed]);

  useEffect(() => {
    try {
      localStorage.setItem('giki_nexus_keys', JSON.stringify(storedKeys));
    } catch {
      // storage error
    }
  }, [storedKeys]);

  const toggleSave = (item: Omit<SavedItem, 'savedAt'>) => {
    setSavedItems((prev) => {
      const exists = prev.some((i) => i.id === item.id);
      if (exists) {
        return prev.filter((i) => i.id !== item.id);
      }
      return [{ ...item, savedAt: new Date().toISOString() }, ...prev];
    });
  };

  const isSaved = (id: string) => savedItems.some((i) => i.id === id);

  const addRecentlyViewed = (item: Omit<RecentlyViewedItem, 'viewedAt'>) => {
    setRecentlyViewed((prev) => {
      const filtered = prev.filter((i) => i.id !== item.id);
      return [{ ...item, viewedAt: new Date().toISOString() }, ...filtered].slice(0, 20);
    });
  };

  const saveKey = (keyInfo: StoredKey) => {
    setStoredKeys((prev) => {
      const filtered = prev.filter((k) => k.entityId !== keyInfo.entityId);
      return [keyInfo, ...filtered];
    });
  };

  const removeKey = (entityId: string) => {
    setStoredKeys((prev) => prev.filter((k) => k.entityId !== entityId));
  };

  return (
    <SavedContext.Provider
      value={{
        savedItems,
        toggleSave,
        isSaved,
        recentlyViewed,
        addRecentlyViewed,
        storedKeys,
        saveKey,
        removeKey,
      }}
    >
      {children}
    </SavedContext.Provider>
  );
};

export const useSaved = () => {
  const context = useContext(SavedContext);
  if (!context) {
    throw new Error('useSaved must be used within a SavedProvider');
  }
  return context;
};
