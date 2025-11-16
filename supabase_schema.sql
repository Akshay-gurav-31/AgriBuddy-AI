-- ============================================

-- COMPLETE SQL SETUP FOR AGRICULTURE CHATBOT

-- ============================================


-- Create function for updating updated_at timestamp

CREATE OR REPLACE FUNCTION public.update_updated_at_column()

RETURNS TRIGGER

LANGUAGE plpgsql

SECURITY DEFINER

SET search_path TO 'public'

AS $$

BEGIN

  NEW.updated_at = now();

  RETURN NEW;

END;

$$;


-- ============================================

-- CONVERSATIONS TABLE

-- ============================================


CREATE TABLE public.conversations (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  title text NOT NULL DEFAULT 'New Chat'::text,
  user_id uuid NOT NULL
);


-- Enable RLS on conversations

ALTER TABLE public.conversations ENABLE ROW LEVEL SECURITY;


-- RLS Policies for conversations

CREATE POLICY "Users can view their own conversations" 
  ON public.conversations FOR SELECT 
  USING (auth.uid() = user_id);


CREATE POLICY "Users can create their own conversations" 
  ON public.conversations FOR INSERT 
  WITH CHECK (auth.uid() = user_id);


CREATE POLICY "Users can update their own conversations" 
  ON public.conversations FOR UPDATE 
  USING (auth.uid() = user_id);


CREATE POLICY "Users can delete their own conversations" 
  ON public.conversations FOR DELETE 
  USING (auth.uid() = user_id);


-- ============================================

-- MESSAGES TABLE

-- ============================================


CREATE TABLE public.messages (
  id uuid NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  conversation_id uuid NOT NULL,
  role text NOT NULL,
  content text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now()
);


-- Enable RLS on messages

ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;


-- RLS Policies for messages

CREATE POLICY "Users can view messages in their conversations" 
  ON public.messages FOR SELECT 
  USING (
    EXISTS (
      SELECT 1 FROM conversations 
      WHERE conversations.id = messages.conversation_id 
      AND conversations.user_id = auth.uid()
    )
  );


CREATE POLICY "Users can create messages in their conversations" 
  ON public.messages FOR INSERT 
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM conversations 
      WHERE conversations.id = messages.conversation_id 
      AND conversations.user_id = auth.uid()
    )
  );


-- Function to update conversation timestamp when message is added

CREATE OR REPLACE FUNCTION public.update_conversation_timestamp()

RETURNS TRIGGER

LANGUAGE plpgsql

SECURITY DEFINER

SET search_path TO 'public'

AS $$

BEGIN

  UPDATE public.conversations

  SET updated_at = now()

  WHERE id = NEW.conversation_id;

  RETURN NEW;

END;

$$;


-- Trigger to update conversation timestamp

CREATE TRIGGER update_conversation_timestamp_trigger
  AFTER INSERT ON public.messages
  FOR EACH ROW
  EXECUTE FUNCTION public.update_conversation_timestamp();


-- ============================================

-- PROFILES TABLE

-- ============================================


CREATE TABLE public.profiles (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL UNIQUE,
  full_name text,
  phone_number text,
  state text,
  city text,
  region text,
  crops jsonb DEFAULT '[]'::jsonb,
  land_area numeric,
  land_unit text DEFAULT 'acre',
  past_cultivation text,
  future_plans text,
  water_source text,
  soil_type text,
  current_crops text,
  preferred_crops text,
  preferred_language text DEFAULT 'hi',
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now()
);


-- Enable RLS on profiles

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;


-- RLS Policies for profiles

CREATE POLICY "Users can view their own profile"
  ON public.profiles FOR SELECT
  USING (auth.uid() = user_id);


CREATE POLICY "Users can insert their own profile"
  ON public.profiles FOR INSERT
  WITH CHECK (auth.uid() = user_id);


CREATE POLICY "Users can update their own profile"
  ON public.profiles FOR UPDATE
  USING (auth.uid() = user_id);


-- Trigger for profiles updated_at

CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();


-- ============================================

-- ENABLE REALTIME (OPTIONAL)

-- ============================================


-- Uncomment the line below if you want real-time updates for messages

-- ALTER PUBLICATION supabase_realtime ADD TABLE public.messages;


-- ============================================

-- INDEXES FOR BETTER PERFORMANCE (OPTIONAL)

-- ============================================


CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
  ON public.messages(conversation_id);


CREATE INDEX IF NOT EXISTS idx_messages_created_at 
  ON public.messages(created_at);


CREATE INDEX IF NOT EXISTS idx_conversations_user_id 
  ON public.conversations(user_id);


CREATE INDEX IF NOT EXISTS idx_conversations_updated_at 
  ON public.conversations(updated_at DESC);


CREATE INDEX IF NOT EXISTS idx_profiles_user_id 
  ON public.profiles(user_id);