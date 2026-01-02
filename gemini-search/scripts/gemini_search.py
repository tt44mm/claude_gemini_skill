#!/usr/bin/env python3
"""
Gemini AI Search with Google Search Grounding & Deep Research
Uses Google's Gemini API with built-in Google Search for real-time information.

Modes:
  - search: Fast grounded search (default)
  - deep: Deep Research Agent for comprehensive multi-step research
"""

import argparse
import json
import os
import sys
import time

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
            "google-genai", "-q"
        ])
        return True


def deep_research(
    query: str,
    api_key: str = None,
    max_wait_seconds: int = 600,
    poll_interval: int = 5
) -> dict:
    """
    Perform deep research using Gemini Deep Research Agent.
    This is an asynchronous operation that can take several minutes.
    
    Args:
        query: The research question/topic
        api_key: Google AI API key
        max_wait_seconds: Maximum time to wait for results (default: 10 min)
        poll_interval: Seconds between status checks
    
    Returns:
        Dictionary with research results
    """
    check_dependencies()
    
    from google import genai
    
    api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key required. Set GEMINI_API_KEY environment variable.")
    
    client = genai.Client(api_key=api_key)
    
    print(f"🔬 Starting Deep Research... (may take several minutes)", file=sys.stderr)
    print(f"📝 Query: {query}", file=sys.stderr)
    
    start_time = time.time()
    interaction_id = None
    result_text = ""
    sources = []
    
    try:
        # Start deep research with streaming
        stream = client.interactions.create(
            input=query,
            agent="deep-research-pro-preview-12-2025",
            background=True,
            stream=True,
        )
        
        # Process streaming events
        for event in stream:
            elapsed = int(time.time() - start_time)
            
            if event.event_type == "interaction.start":
                interaction_id = event.id
                print(f"📋 Research ID: {interaction_id} [{elapsed}s]", file=sys.stderr)
            
            elif event.event_type == "interaction.thinking":
                # Show thinking progress
                if hasattr(event, 'delta') and event.delta:
                    if hasattr(event.delta, 'content') and event.delta.content:
                        if hasattr(event.delta.content, 'text') and event.delta.content.text:
                            thought = event.delta.content.text.strip()
                            if thought:
                                # Truncate long thoughts for display
                                display = thought[:80] + "..." if len(thought) > 80 else thought
                                print(f"💭 [{elapsed}s] {display}", file=sys.stderr)
            
            elif event.event_type == "interaction.complete":
                print(f"✅ Research complete! [{elapsed}s]", file=sys.stderr)
                
                # Extract final result
                if hasattr(event, 'interaction') and event.interaction:
                    interaction = event.interaction
                    
                    # Get output content
                    if hasattr(interaction, 'output') and interaction.output:
                        for part in interaction.output:
                            if hasattr(part, 'text') and part.text:
                                result_text += part.text
                    
                    # Try to get sources from grounding metadata
                    if hasattr(interaction, 'grounding_metadata') and interaction.grounding_metadata:
                        gm = interaction.grounding_metadata
                        if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                            for chunk in gm.grounding_chunks:
                                if hasattr(chunk, 'web') and chunk.web:
                                    sources.append({
                                        'title': getattr(chunk.web, 'title', 'Source'),
                                        'uri': getattr(chunk.web, 'uri', '')
                                    })
                break
            
            elif event.event_type == "interaction.error":
                error_msg = "Unknown error"
                if hasattr(event, 'error') and event.error:
                    error_msg = str(event.error)
                raise Exception(f"Research failed: {error_msg}")
            
            # Check timeout
            if time.time() - start_time > max_wait_seconds:
                raise TimeoutError(f"Research timed out after {max_wait_seconds} seconds")
        
    except Exception as e:
        if "deadline_exceeded" in str(e).lower() or "timeout" in str(e).lower():
            raise TimeoutError(f"Research timed out. Try a simpler query or increase --timeout")
        raise
    
    if not result_text:
        result_text = "Research completed but no output was generated."
    
    return {
        'response': result_text,
        'sources': sources,
        'metadata': {
            'mode': 'deep_research',
            'query': query,
            'interaction_id': interaction_id,
            'duration_seconds': int(time.time() - start_time)
        }
    }


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
            
            # Extract grounding chunks (sources)
            if hasattr(grounding_metadata, 'grounding_chunks'):
                for chunk in grounding_metadata.grounding_chunks:
                    if hasattr(chunk, 'web'):
                        sources.append({
                            'title': getattr(chunk.web, 'title', 'Unknown'),
                            'uri': getattr(chunk.web, 'uri', '')
                        })
    
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
        mode = result['metadata'].get('mode', 'search')
        title = "Deep Research Result" if mode == 'deep_research' else "Gemini Search Result"
        
        output = f"## {title}\n\n"
        output += f"**Query:** {result['metadata']['query']}\n\n"
        
        if mode == 'deep_research' and 'duration_seconds' in result['metadata']:
            output += f"**Duration:** {result['metadata']['duration_seconds']} seconds\n\n"
        
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
        description="Gemini AI Search with Google Search Grounding & Deep Research",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick grounded search (default)
  python gemini_search.py "Latest AI news"
  
  # Deep research (takes 2-5 minutes, comprehensive)
  python gemini_search.py "Analyze the impact of AI on education" --mode deep
  
  # JSON output for parsing
  python gemini_search.py "Query" --format json
  
  # Use specific model for search
  python gemini_search.py "Query" --model gemini-2.5-pro
"""
    )
    parser.add_argument("query", help="Search query or research question")
    parser.add_argument(
        "--mode", "-M",
        choices=["search", "deep"],
        default="search",
        help="search=fast grounded search, deep=comprehensive research agent (default: search)"
    )
    parser.add_argument(
        "--model", "-m",
        default="gemini-2.5-flash",
        help="Gemini model for search mode (default: gemini-2.5-flash)"
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
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Max wait time for deep research in seconds (default: 600)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "deep":
            result = deep_research(
                query=args.query,
                api_key=args.api_key,
                max_wait_seconds=args.timeout
            )
        else:
            result = gemini_search(
                query=args.query,
                model=args.model,
                api_key=args.api_key,
                output_format=args.format,
                include_sources=not args.no_sources
            )
        print(format_output(result, args.format))
    except KeyboardInterrupt:
        print("\n⚠️ Research cancelled by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
