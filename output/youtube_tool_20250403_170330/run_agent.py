#!/usr/bin/env python3
import os
import sys
import asyncio
import logging
import argparse
from crewai.tools import YouTubeTranscriptMCPMCPTool

def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler()
        ]
    )

async def run_agent(video_url: str):
    tool = YouTubeTranscriptMCPMCPTool()
    try:
        logging.info("Fetching transcript for video: %s", video_url)
        transcript = await tool.get_transcript(video_url)
        print("Transcript:\n", transcript)
    except Exception as e:
        logging.error("Error fetching transcript: %s", str(e))

def main():
    parser = argparse.ArgumentParser(description="Run a YouTube transcript agent.")
    parser.add_argument("video_url", nargs='?', help="YouTube video URL")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("-o", "--output", type=str, help="Specify output file path")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if not args.video_url:
        video_url = input("Please enter the YouTube video URL: ")
    else:
        video_url = args.video_url

    try:
        asyncio.run(run_agent(video_url))
    except Exception as e:
        logging.error("An unexpected error occurred: %s", str(e))

if __name__ == "__main__":
    main()