-- Enable the vector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the agent_templates table
CREATE TABLE IF NOT EXISTS agent_templates (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    folder_name text NOT NULL,
    agents_code text,
    tools_code text,
    tasks_code text,
    crew_code text,
    purpose text,
    metadata jsonb,
    embedding vector(1536),
    created_at timestamp with time zone DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create the matching function
CREATE OR REPLACE FUNCTION match_agent_templates(query_embedding vector(1536), match_threshold float, match_count int)
RETURNS TABLE (
    id bigint,
    folder_name text,
    agents_code text,
    tools_code text,
    tasks_code text,
    crew_code text,
    purpose text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id,
        t.folder_name,
        t.agents_code,
        t.tools_code,
        t.tasks_code,
        t.crew_code,
        t.purpose,
        t.metadata,
        1 - (t.embedding <=> query_embedding) as similarity
    FROM agent_templates t
    WHERE 1 - (t.embedding <=> query_embedding) > match_threshold
    ORDER BY t.embedding <=> query_embedding
    LIMIT match_count;
END;
$$; 