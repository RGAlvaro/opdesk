/// <reference types="vite/client" />

// Vite raw imports let public pages render static repository content.
declare module "*.md?raw" {
  const content: string;
  export default content;
}
