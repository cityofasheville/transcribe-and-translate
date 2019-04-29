# ==================================================================================
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ==================================================================================
#
# translatevideo.py
# by: Rob Dachowski
# For questions or feedback, please contact robdac@amazon.com
# 
# Purpose: This code drives the process to create a transription job, translate it into another language,
#          create subtitles, use Amazon Polly to synthesize an alternate audio track, and finally put it all together
#          into a new video.
#
# Change Log:
#          6/29/2018: Initial version
#
# ==================================================================================


import argparse
import boto3
import botocore
from transcribeUtils import *
from srtUtils import *
import time
from videoUtils import *
from audioUtils import *
import json

# Get the command line arguments and parse them
parser = argparse.ArgumentParser( prog='translatevideo.py', description='Process a video found in the input file, process it, and write tit out to the output file')
parser.add_argument('-region', required=True, help="The AWS region containing the S3 buckets" )
parser.add_argument('-inbucket', required=True, help='The S3 bucket containing the input file')
parser.add_argument('-infile', required=True, help='The input file to process')
parser.add_argument('-outbucket', required=True, help='The S3 bucket containing the input file')
parser.add_argument('-outfilename', required=True, help='The file name without the extension')
parser.add_argument('-outfiletype', required=True, help='The output file type.  E.g. mp4, mov')
parser.add_argument('-outlang', required=True, nargs='+', help='The language codes for the desired output.  E.g. en = English, de = German')		
args = parser.parse_args()

# print out parameters and key header information for the user
print( "==> translatevideo.py:\n")
print( "==> Parameters: ")
print("\tInput bucket/object: " + args.inbucket + args.infile )
print( "\tOutput bucket/object: " + args.outbucket + args.outfilename + "." + args.outfiletype )

print( "\n==> Target Language Translation Output: " )

for lang in args.outlang:
	print( "\t" + args.outbucket + args.outfilename + "-" + lang + "." + args.outfiletype)
	
# Now get the transcript JSON from AWS Transcribe

with open('CC-Budget-Worksession-111318-Transcript.json', 'r') as f:
  transcriptJSON = json.load(f)
#print( "\n==> Transcript: \n" + transcript)

# Create the SRT File for the original transcript and write it out.  
#writeTranscriptToSRT( transcript, 'en', "subtitles-en.srt" )  
#createVideo( args.infile, "subtitles-en.srt", args.outfilename + "-en." + args.outfiletype, "audio-en.mp3", True)

# Now write out the translation to the transcript for each of the target languages
for lang in args.outlang:
	#writeTranslationToSRT(json.dumps(transcriptJSON), 'en', lang, "subtitles-" + lang + ".srt", args.region ) 	
	translation = translateTranscript( json.dumps(transcriptJSON), 'en', lang, args.region )
	mapTranslationAndWriteToSRT(translation, "subtitles-en.srt", lang, args.region, "subtitles-" + lang + ".srt")

	#Now that we have the subtitle files, let's create the audio track
	#createAudioTrackFromTranslation( args.region, json.dumps(transcriptJSON), 'en', lang, "audio-" + lang + ".mp3" )

	# Finally, create the composited videos
	#subtitles only
#	createVideo( args.infile, "subtitles-" + lang + ".srt", args.outfilename + "-subtitles-" + lang + "." + args.outfiletype, "audio-" + lang + ".mp3", True)
	#english subtitles and other lang voiceover
	#if lang != 'en':
	#	createVideoVoiceOverOnly( args.infile[0:-4] + "-ac-subtitles-en.mp4", "subtitles-en.srt", args.outfilename + "-voiceover-" + lang + "." + args.outfiletype, "audio-" + lang + ".mp3", False)

	
	
	


	
