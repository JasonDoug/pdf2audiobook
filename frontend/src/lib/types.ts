export interface User {
  id: number
  auth_provider_id: string
  email: string
  first_name: string | null
  last_name: string | null
  subscription_tier: SubscriptionTier
  paddle_customer_id: string | null
  one_time_credits: number
  monthly_credits_used: number
  created_at: string
  updated_at: string | null
}

export enum SubscriptionTier {
  FREE = 'free',
  PRO = 'pro',
  ENTERPRISE = 'enterprise',
}

export enum JobStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum VoiceProvider {
  OPENAI = 'openai',
  GOOGLE = 'google',
  AWS_POLLY = 'aws_polly',
  AZURE = 'azure',
  ELEVEN_LABS = 'eleven_labs',
}

export enum ConversionMode {
  FULL = 'full',
  SUMMARY_EXPLANATION = 'summary_explanation',
}

export interface Job {
  id: number
  user_id: number
  original_filename: string
  pdf_s3_key: string
  audio_s3_key: string | null
  pdf_s3_url: string | null
  audio_s3_url: string | null
  status: JobStatus
  progress_percentage: number
  error_message: string | null
  voice_provider: VoiceProvider
  voice_type: string
  reading_speed: number
  include_summary: boolean
  conversion_mode: ConversionMode
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface Product {
  id: number
  paddle_product_id: string
  name: string
  description: string | null
  type: ProductType
  price: number | null
  currency: string
  credits_included: number | null
  subscription_tier: SubscriptionTier | null
  is_active: boolean
  created_at: string
  updated_at: string | null
}

export enum ProductType {
  SUBSCRIPTION = 'subscription',
  ONE_TIME = 'one_time',
}
