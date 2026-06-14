export type ValidationStatus = "PASS" | "WARNING" | "FAIL";

export interface LabelFields {
  brand_name: string | null;
  class_type: string | null;
  alcohol_content: string | null;
  net_contents: string | null;
  bottler_producer_name: string | null;
  country_of_origin: string | null;
  government_warning: string | null;
}

export interface FieldValidation {
  field: keyof LabelFields;
  expected: string | null;
  extracted: string | null;
  status: ValidationStatus;
  confidence: number;
  message: string;
}

export interface OCRResult {
  text: string;
  confidence: number;
  engine: string;
  processing_ms: number;
  fields: LabelFields;
  format_observations?: {
    government_warning_prefix_bold: boolean | null;
    source: string;
  };
}

export interface LabelReviewResult {
  result_id: string;
  filename: string;
  application_id: string;
  status: ValidationStatus;
  uploaded_at: string;
  image_url?: string;
  ocr: OCRResult;
  validations: FieldValidation[];
}

export interface BatchResponse {
  batch_id: string;
  results: LabelReviewResult[];
  summary: {
    total: number;
    pass: number;
    warning: number;
    fail: number;
  };
}
