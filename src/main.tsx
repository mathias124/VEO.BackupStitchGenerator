import React from 'react';
import ReactDOM from 'react-dom/client'; // Use createRoot from React 18
import Root from './root.tsx'; // Make sure the path is correct and matches your file name

const root = ReactDOM.createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>
);
