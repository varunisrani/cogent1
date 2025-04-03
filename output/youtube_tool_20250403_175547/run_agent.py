#!/usr/bin/env python3
import os
import asyncio
import logging
import sys
from crewai.tools import YouTubeTranscriptMCPMCPTool
from dotenv import load_dotenv
import argparse

load_dotenv()

def setup_logging(verbose=False):
    """Set up logging for the YouTube transcription agent."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()]
    )

async def run_agent(video_url):
    """Run the YouTube transcription agent."""
    try:
        tool = YouTubeTranscriptMCPMCPTool()
        logging.info("Starting transcription for: %s", video_url)
        transcript = await tool.transcribe(video_url)
        print("Transcription:\n", transcript)
    except Exception as e:
        logging.error("Error during transcription: %s", str(e))

def main():
    parser = argparse.ArgumentParser(description="Run a YouTube transcription agent.")
    parser.add_argument("video_url", nargs='?', help="YouTube video URL for transcription")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-o", "--output", help="Output file path for transcription text")
    
    args = parser.parse_args()
    setup_logging(args.verbose)

    if not args.video_url:
        args.video_url = input("Enter YouTube video URL: ")

    asyncio.run(run_agent(args.video_url))

if __name__ == "__main__":
    main()