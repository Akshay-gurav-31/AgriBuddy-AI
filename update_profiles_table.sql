-- SQL commands to update the profiles table with new columns for personalized profile feature

-- Add new columns to the profiles table
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS future_plans TEXT,
ADD COLUMN IF NOT EXISTS land_unit TEXT DEFAULT 'acre',
ADD COLUMN IF NOT EXISTS current_crops TEXT,
ADD COLUMN IF NOT EXISTS preferred_crops TEXT;

-- Update existing records to set default land_unit if null
UPDATE public.profiles 
SET land_unit = 'acre' 
WHERE land_unit IS NULL;

-- Grant necessary permissions for the new columns
GRANT SELECT, INSERT, UPDATE ON public.profiles TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.profiles TO anon;

-- Create indexes for better performance on new columns
CREATE INDEX IF NOT EXISTS idx_profiles_current_crops ON public.profiles(current_crops);
CREATE INDEX IF NOT EXISTS idx_profiles_preferred_crops ON public.profiles(preferred_crops);