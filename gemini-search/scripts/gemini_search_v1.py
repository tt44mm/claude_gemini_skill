#!/usr/bin/env python3
"""
Gemini AI Search with Google Search Grounding
Uses Google's Gemini API with built-in Google Search for real-time information.
"""

import argparse
import json
import os
import sys

def check_dependencies():
    """Check if google-genai is installed, install if not."""
    try:
        from google import genai
        return True
    except ImportError:
        print("Installing google-genai...", file=sys.stderr)
        import subprocess
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "google-genai", "--break-system-packages", "-q"
        ])
        return True

def gemini_search(
    query: str,
    model: str = "gemini-2.5-flash",
    api_key: str = None,
    output_format: str = "text",
    include_sources: bool = True
) -> dict:
    """
    Perform a search using Gemini with Google Search grounding.
    
    Args:
        query: The search query/question
        model: Gemini model to use (default: gemini-2.5-flash)
        api_key: Google AI API key (or set GEMINI_API_KEY env var)
        output_format: "text", "json", or "markdown"
        include_sources: Whether to include source citations
    
    Returns:
        Dictionary with 'response', 'sources', and 'metadata'
    """
    check_dependencies()
    
    from google import genai
    from google.genai import types
    
    # Get API key
    api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "API key required. Set GEMINI_API_KEY environment variable or pass api_key parameter.\n"
            "Get your API key at: https://aistudio.google.com/apikey"
        )
    
    # Initialize client
    client = genai.Client(api_key=api_key)
    
    # Configure Google Search grounding
    grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
    )
    
    config = types.GenerateContentConfig(
        tools=[grounding_tool]
    )
    
    # Make request
    response = client.models.generate_content(
        model=model,
        contents=query,
        config=config,
    )
    
    # Extract response text
    response_text = response.text if hasattr(response, 'text') else str(response)
    
    # Extract grounding metadata and sources
    sources = []
    grounding_metadata = None
    
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata'):
            grounding_metadata = candidate.grounding_metadata
            
            # Extract search entry point (rendered search link)
            if hasattr(grounding_metadata, 'search_entry_point'):
                sep = grounding_metadata.search_entry_point
                if hasattr(sep, 'rendered_content'):
                    pass  # HTML snippet available
            
            # Extract grounding chunks (sources)
            if hasattr(grounding_metadata, 'grounding_chunks'):
                for chunk in grounding_metadata.grounding_chunks:
                    if hasattr(chunk, 'web'):
                        sources.append({
                            'title': getattr(chunk.web, 'title', 'Unknown'),
                            'uri': getattr(chunk.web, 'uri', '')
                        })
            
            # Extract grounding supports (specific citations)
            if hasattr(grounding_metadata, 'grounding_supports'):
                for support in grounding_metadata.grounding_supports:
                    # Each support links text segments to source chunks
                    pass
    
    result = {
        'response': response_text,
        'sources': sources if include_sources else [],
        'metadata': {
            'model': model,
            'query': query,
            'has_grounding': grounding_metadata is not None
        }
    }
    
    return result


def format_output(result: dict, output_format: str) -> str:
    """Format the result based on output format preference."""
    if output_format == "json":
        return json.dumps(result, indent=2, ensure_ascii=False)
    
    elif output_format == "markdown":
        output = f"## Gemini Search Result\n\n"
        output += f"**Query:** {result['metadata']['query']}\n\n"
        output += f"### Response\n\n{result['response']}\n\n"
        
        if result['sources']:
            output += "### Sources\n\n"
            for i, source in enumerate(result['sources'], 1):
                output += f"{i}. [{source['title']}]({source['uri']})\n"
        
        return output
    
    else:  # text
        output = result['response']
        if result['sources']:
            output += "\n\n---\nSources:\n"
            for source in result['sources']:
                output += f"- {source['title']}: {source['uri']}\n"
        return output


def main():
    parser = argparse.ArgumentParser(
        description="Gemini AI Search with Google Search Grounding"
    )
    parser.add_argument("query", help="Search query or question")
    parser.add_argument(
        "--model", "-m",
        default="gemini-2.5-flash",
        help="Gemini model (default: gemini-2.5-flash)"
    )
    parser.add_argument(
        "--api-key", "-k",
        help="Google AI API key (or set GEMINI_API_KEY env var)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text)"
    )
    parser.add_argument(
        "--no-sources",
        action="store_true",
        help="Exclude source citations"
    )
    
    args = parser.parse_args()
    
    try:
        result = gemini_search(
            query=args.query,
            model=args.model,
            api_key=args.api_key,
            output_format=args.format,
            include_sources=not args.no_sources
        )
        print(format_output(result, args.format))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
