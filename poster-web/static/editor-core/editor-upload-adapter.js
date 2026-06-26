import { uploadFile } from "../shared/upload.js";

export function createEditorUploadAdapter(options = {}) {
  return {
    async uploadImage(file) {
      return uploadFile(file, { ...options, assetType: "module_content_image" });
    },
  };
}
