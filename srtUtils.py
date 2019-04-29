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
# srtUtils.py
# by: Rob Dachowski
# For questions or feedback, please contact robdac@amazon.com
# 
# Purpose: The program provides a number of utility functions for creating SubRip Subtitle files (.SRT)
#
# Change Log:
#          6/29/2018: Initial version
#
# ==================================================================================

import json
import boto3
import re
import codecs
import math
from audioUtils import *



# ==================================================================================
# Function: newPhrase
# Purpose: simply create a phrase tuple
# Parameters: 
#                 None
# ==================================================================================
def newPhrase():
	return { 'start_time': '', 'end_time': '', 'words' : [] }


	
# ==================================================================================
# Function: getTimeCode
# Purpose: Format and return a string that contains the converted number of seconds into SRT format
# Parameters: 
#                 seconds - the duration in seconds to convert to HH:MM:SS,mmm 
# ==================================================================================	
	# Format and return a string that contains the converted number of seconds into SRT format
def getTimeCode( seconds ):
	t_hund = int(seconds % 1 * 1000)
	t_seconds = int( seconds )
	t_secs = ((float( t_seconds) / 60) % 1) * 60
	t_mins = int( t_seconds / 60 )
	return str( "%02d:%02d:%02d,%03d" % (00, t_mins, int(t_secs), t_hund ))
	

# ==================================================================================
# Function: writeTranscriptToSRT
# Purpose: Function to get the phrases from the transcript and write it out to an SRT file
# Parameters: 
#                 transcript - the JSON output from Amazon Transcribe
#                 sourceLangCode - the language code for the original content (e.g. English = "EN")
#                 srtFileName - the name of the SRT file (e.g. "mySRT.SRT")
# ==================================================================================	
def writeTranscriptToSRT( transcript, sourceLangCode, srtFileName ):
	# Write the SRT file for the original language
	print( "==> Creating SRT from transcript")
	phrases = getPhrasesFromTranscript( transcript )
	writeSRT( phrases, srtFileName )
	

# ==================================================================================
# Function: writeTranscriptToSRT
# Purpose: Based on the JSON transcript provided by Amazon Transcribe, get the phrases from the translation 
#          and write it out to an SRT file
# Parameters: 
#                 transcript - the JSON output from Amazon Transcribe
#                 sourceLangCode - the language code for the original content (e.g. English = "EN")
#                 targetLangCode - the language code for the translated content (e.g. Spanich = "ES")
#                 srtFileName - the name of the SRT file (e.g. "mySRT.SRT")
# ==================================================================================
def writeTranslationToSRT( transcript, sourceLangCode, targetLangCode, srtFileName, region ):
	# First get the translation
	print( "\n\n==> Translating from " + sourceLangCode + " to " + targetLangCode )
	translation = translateTranscript( transcript, sourceLangCode, targetLangCode, region )
	# Now create phrases from the translation
	textToTranslate = str(translation["TranslatedText"])
	#phrases = getPhrasesFromTranslation( textToTranslate, targetLangCode )
	#writeSRT( phrases, srtFileName )

# ==================================================================================
# Function: getPhrasesFromTranslation
# Purpose: Based on the JSON translation provided by Amazon Translate, get the phrases from the translation 
#          and write it out to an SRT file.  Note that since we are using a block of translated text rather than
#          a JSON structure with the timing for the start and end of each word as in the output of Transcribe,
#          we will need to calculate the start and end-time for each phrase
# Parameters: 
#                 translation - the JSON output from Amazon Translate
#                 targetLangCode - the language code for the translated content (e.g. Spanich = "ES")
# ==================================================================================	
def getPhrasesFromTranslation( translation, targetLangCode ):

	# Now create phrases from the translation
	words = translation.split()
	
	#print( words ) #debug statement
	
	#set up some variables for the first pass
	phrase =  newPhrase()
	phrases = []
	nPhrase = True
	x = 0
	c = 0
	seconds = 0

	print("==> Creating phrases from translation...")

	for word in words:

		# if it is a new phrase, then get the start_time of the first item
		if nPhrase == True:
			phrase["start_time"] = getTimeCode( seconds )
			nPhrase = False
			c += 1
				
		# Append the word to the phrase...
		phrase["words"].append(word)
		x += 1
		
		
		# now add the phrase to the phrases, generate a new phrase, etc.
		if x == 10:
		
			# For Translations, we now need to calculate the end time for the phrase
			psecs = getSecondsFromTranslation( getPhraseText( phrase), targetLangCode, "phraseAudio" + str(c) + ".mp3" ) 
			seconds += psecs
			phrase["end_time"] = getTimeCode( seconds )
		
			#print c, phrase
			phrases.append(phrase)
			phrase = newPhrase()
			nPhrase = True
			#seconds += .001
			x = 0
			
		# This if statement is to address a defect in the SubtitleClip.   If the Subtitles end up being
		# a different duration than the content, MoviePy will sometimes fail with unexpected errors while
		# processing the subclip.   This is limiting it to something less than the total duration for our example
		# however, you may need to modify or eliminate this line depending on your content.
		#if c == 30:
		#	break
			
	return phrases
	

# ==================================================================================
# Function: getPhrasesFromTranscript
# Purpose: Based on the JSON transcript provided by Amazon Transcribe, get the phrases from the translation 
#          and write it out to an SRT file
# Parameters: 
#                 transcript - the JSON output from Amazon Transcribe
# ==================================================================================
def getPhrasesFromTranscript( transcript ):

	# This function is intended to be called with the JSON structure output from the Transcribe service.  However,
	# if you only have the translation of the transcript, then you should call getPhrasesFromTranslation instead

	# Now create phrases from the translation
	ts = json.loads( transcript )
	items = ts['results']['items']
	#print( items )
	
	#set up some variables for the first pass
	phrase =  newPhrase()
	phrases = []
	nPhrase = True
	x = 0
	c = 0

	print("==> Creating phrases from transcript...")

	for item in items:

		# if it is a new phrase, then get the start_time of the first item
		if nPhrase == True:
			if item["type"] == "pronunciation":
				phrase["start_time"] = getTimeCode( float(item["start_time"]) )
				nPhrase = False
			c+= 1
		else:	
			# get the end_time if the item is a pronuciation and store it
			# We need to determine if this pronunciation or puncuation here
			# Punctuation doesn't contain timing information, so we'll want
			# to set the end_time to whatever the last word in the phrase is.
			if item["type"] == "pronunciation":
				phrase["end_time"] = getTimeCode( float(item["end_time"]) )
				
		# in either case, append the word to the phrase...
		phrase["words"].append(item['alternatives'][0]["content"])
		x += 1
		
		# now add the phrase to the phrases, generate a new phrase, etc.
		if x == 10:
			#print c, phrase
			phrases.append(phrase)
			phrase = newPhrase()
			nPhrase = True
			x = 0
			
	return phrases

#new function for translation to SRT
def mapTranslationAndWriteToSRT(translation, sourceLangSRTFileName, targetLangCode, region, targetLangSRTFileName):
	phrases = []
	tempObject = []
	originalWordCount = 0
	with open(sourceLangSRTFileName) as orig:
		for line in orig:
			l = line.strip()
			if len(l) != 0:
				tempObject.append(l)
			else:
				phrases.append(tempObject[:])
				originalWordCount = originalWordCount + len(tempObject[2].split())
				tempObject = []
	if len(phrases) > 0:
		duration = phrases[-1][1].split(' --> ')[1]
	
	hr, min, sec = duration.split(':')
	sec, ms = sec.split(',')
	ms = int(hr) * 60 * 60 * 1000 + int(min) * 60 * 1000 + int(sec) * 1000

	#Calculate time percent of each phrase out of total time
	#also calculate the word percents
	phraseTimePercents = []
	phraseWordPercents = []
	for p in phrases:
		startTime, endTime = p[1].split(' --> ')
		startHr, startMin, startSec = startTime.split(':')
		startSec, startMS = startSec.split(',')
		startMS = int(startHr) * 60 * 60 * 1000 + int(startMin) * 60 * 1000 + int(startSec) * 1000
		endHr, endMin, endSec = endTime.split(':')
		endSec, endMS = endSec.split(',')
		endMS = int(endHr) * 60 * 60 * 1000 + int(endMin) * 60 * 1000 + int(endSec) * 1000
		phraseTimePercent = (endMS - startMS) / ms
		phraseTimePercents.append(phraseTimePercent)
		phraseWordPercent = len(p[2].split()) / originalWordCount
		phraseWordPercents.append(phraseWordPercent)

	translationText = translation["TranslatedText"]
	allTranslatedWords = translationText.split()
	numTranslatedWords = len(allTranslatedWords)

	#split the translated words up
	translatedPhrases = []
	startIndex = 0
	endIndex = 0
	for i in range(0, len(phraseWordPercents)):
		if targetLangCode == 'es':
			if i % 5 == 0: #TODO: verify if this mods distribution is transferable to other videos!
				phraseWordCount = math.ceil(phraseWordPercents[i] * numTranslatedWords)
			else:
				phraseWordCount = math.floor(phraseWordPercents[i] * numTranslatedWords)
		elif targetLangCode == 'ru': #TODO: verify if these silly mods are transferable to other videos!
			if i % 2 == 0:
				phraseWordCount = math.floor(phraseWordPercents[i] * numTranslatedWords) + 1
			elif i % 3 == 0:
				phraseWordCount = math.floor(phraseWordPercents[i] * numTranslatedWords) + 1
			elif i % 5 == 0:
				phraseWordCount = math.floor(phraseWordPercents[i] * numTranslatedWords) + 1
			else:
				phraseWordCount = math.floor(phraseWordPercents[i] * numTranslatedWords)
		else:
			phraseWordCount = math.floor(phraseWordPercents[i] * numTranslatedWords)
		endIndex = startIndex + phraseWordCount
		if endIndex > numTranslatedWords:
			endIndex = numTranslatedWords
		translatedPhrases.append([phrases[i][0], phrases[i][1], ' '.join(allTranslatedWords[startIndex:endIndex])])
		startIndex = endIndex
	if endIndex < numTranslatedWords:
		translatedPhrases[-1][2] = translatedPhrases[-1][2] + ' ' + ' '.join(allTranslatedWords[endIndex:len(allTranslatedWords)])
	print(originalWordCount, numTranslatedWords)

	#for tp in translatedPhrases:
	#	print(tp)

	print("==> Writing phrases to disk...")
	#e = codecs.open(filename,"w+", "utf-8")
	if targetLangCode == "es":
		e = codecs.open(targetLangSRTFileName,"w+", "cp1252")
	elif targetLangCode == "ru":
		e = codecs.open(targetLangSRTFileName,"w+", "cp1251")
	else:
		e = codecs.open(filename,"w+", "utf-8")

	x = 1
	
	for t in translatedPhrases:
		# write out the phrase number
		e.write( t[0] + "\n" )
		
		# write out the start and end time
		e.write( t[1] + "\n" )
					
		# write out the srt file
		e.write(t[2] + "\n\n" )
	e.close()

# ==================================================================================
# Function: translateTranscriptSRTtoSRT
# Purpose: Based on the srt file get a translation that is better timed and make new SRT
# Parameters: 
#                 transcriptSRT - the srt file in source language
#                 sourceLangCode - the language code for the original content (e.g. English = "EN")
#                 targetLangCode - the language code for the translated content (e.g. Spanich = "ES")
#                 region - the AWS region in which to run the Translation (e.g. "us-east-1")
#									srtFileName - fileName for the SRT to write to
# ==================================================================================
def translateTranscriptSRTtoSRT( transcriptSRT, sourceLangCode, targetLangCode, region , srtFileName):
	# Get the translation in the target language.  We want to do this for multiple phrases from the SRT
	# at a time. This really matters in some lanaguages
	phrases = []
	counter = 0
	tempObject = []
	with open(transcriptSRT) as orig:
		for line in orig:
			l = line.strip()
			if len(l) != 0:
				tempObject.append(l)
			else:
				phrases.append(tempObject[:])
				tempObject = []

	#set up the Amazon Translate client
	translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)
	
	# call Translate  with the text, source language code, and target language code.  The result is a JSON structure containing
	# the translated text
	# Have to do this by sentence chunks because there can only be 5000 bytes sent at once
  
	#try fifty phrases from srt at a time
	chunkLen = 50
	chunks = []
	counter = 0
	chunk = ''
	for p in phrases:
		counter = counter + 1
		if counter % chunkLen == 0:
			chunks.append(chunk)
			counter = 0
			chunk = ''
		else:
			chunk = chunk + ' ' + p[2]
	if len(chunk) > 0:
		chunks.append(chunk)

	translatedChunks = []
	for c in chunks:
		translatedChunk = translate.translate_text(Text=c, SourceLanguageCode=sourceLangCode, TargetLanguageCode=targetLangCode)
		translatedChunks.append(translatedChunk["TranslatedText"])

	#now divide translated content into approximate lengths to match original phrase counters
	translatedWithoutTimes = []
	numPhrases = len(phrases)
	allWords = (' '.join(translatedChunks).split())
	numWords = len(allWords)
	wordsPerPhrase = int(round(numWords / numPhrases))
	discrepancy = numWords - (numPhrases * wordsPerPhrase)
	if discrepancy > 0:
		addExtraWordPerEvery = math.ceil(numPhrases / discrepancy) 

	startIndex = 0
	for i in range(0, numPhrases):
		if startIndex + wordsPerPhrase > numWords:
			translatedWithoutTimes.append(' '.join(allWords[startIndex:(startIndex + (numWords - startIndex + wordsPerPhrase))]))
		elif i % addExtraWordPerEvery == 0:
			if startIndex + 1 + wordsPerPhrase < numWords:
				translatedWithoutTimes.append(' '.join(allWords[startIndex:startIndex + wordsPerPhrase + 1]))
				startIndex = startIndex + 1
			else:
				translatedWithoutTimes.append(' '.join(allWords[startIndex:startIndex + wordsPerPhrase]))
		else:
			translatedWithoutTimes.append(' '.join(allWords[startIndex:startIndex + wordsPerPhrase]))
		startIndex = startIndex + wordsPerPhrase

	translatedWithTimes = []
	for i in range(len(phrases)):
		translatedWithTimes.append((phrases[i][0], phrases[i][1], translatedWithoutTimes[i]))

	for t in translatedWithTimes:
		print(t)

	print("==> Writing phrases to disk...")
	#e = codecs.open(filename,"w+", "utf-8")
	e = codecs.open(srtFileName,"w+", "cp1252")
	x = 1
	
	for t in translatedWithTimes:
		# write out the phrase number
		e.write( t[0] + "\n" )
		
		# write out the start and end time
		e.write( t[1] + "\n" )
					
		# write out the srt file
		e.write(t[2] + "\n\n" )
	e.close()

# ==================================================================================
# Function: translateTranscript
# Purpose: Based on the JSON transcript provided by Amazon Transcribe, get the JSON response of translated text
# Parameters: 
#                 transcript - the JSON output from Amazon Transcribe
#                 sourceLangCode - the language code for the original content (e.g. English = "EN")
#                 targetLangCode - the language code for the translated content (e.g. Spanich = "ES")
#                 region - the AWS region in which to run the Translation (e.g. "us-east-1")
# ==================================================================================
def translateTranscript( transcript, sourceLangCode, targetLangCode, region ):
	# Get the translation in the target language.  We want to do this first so that the translation is in the full context
	# of what is said vs. 1 phrase at a time.  This really matters in some lanaguages

	# stringify the transcript
	ts = json.loads( transcript )

	# pull out the transcript text and put it in the txt variable
	txt = ts["results"]["transcripts"][0]["transcript"]
		
	#set up the Amazon Translate client
	translate = boto3.client(service_name='translate', region_name=region, use_ssl=True)
	
	# call Translate  with the text, source language code, and target language code.  The result is a JSON structure containing
	# the translated text
	# Have to do this by sentence chunks because there can only be 5000 bytes sent at once
	sentences = re.split(r'(?<=\.)', txt)
	#print(txt)
  
	translatedChunks = []
	for i in range(0, len(sentences), 10):
		if (len(sentences) - i > 0 and len(sentences) - i < 10):
			chunk = " ".join(sentences[i:i+(len(sentences) - i)])
			translatedChunk = translate.translate_text(Text=chunk, SourceLanguageCode=sourceLangCode, TargetLanguageCode=targetLangCode)
			translatedChunks.append(translatedChunk["TranslatedText"])
		else:
			chunk = " ".join(sentences[i:i+10])
			translatedChunk = translate.translate_text(Text=chunk, SourceLanguageCode=sourceLangCode, TargetLanguageCode=targetLangCode)
			translatedChunks.append(translatedChunk["TranslatedText"])
	#translation = translate.translate_text(Text=txt,SourceLanguageCode=sourceLangCode, TargetLanguageCode=targetLangCode)
	translation = {"TranslatedText": "".join(translatedChunks)} #kind of hacky
	return translation
	
	

# ==================================================================================
# Function: writeSRT
# Purpose: Iterate through the phrases and write them to the SRT file
# Parameters: 
#                 phrases - the array of JSON tuples containing the phrases to show up as subtitles
#                 filename - the name of the SRT output file (e.g. "mySRT.srt")
# ==================================================================================
def writeSRT( phrases, filename ):
	print("==> Writing phrases to disk...")

	# open the files
	#e = codecs.open(filename,"w+", "utf-8")
	e = codecs.open(filename,"w+", "cp1252")
	x = 1
	
	for phrase in phrases:

		# determine how many words are in the phrase
		length = len(phrase["words"])
		
		# write out the phrase number
		e.write( str(x) + "\n" )
		x += 1
		
		# write out the start and end time
		e.write( phrase["start_time"] + " --> " + phrase["end_time"] + "\n" )
					
		# write out the full phase.  Use spacing if it is a word, or punctuation without spacing
		out = getPhraseText( phrase )

		# write out the srt file
		e.write(out + "\n\n" )
		

		#print out
		
	e.close()
	

# ==================================================================================
# Function: getPhraseText
# Purpose: For a given phrase, return the string of words including punctuation
# Parameters: 
#                 phrase - the array of JSON tuples containing the words to show up as subtitles
# ==================================================================================

def getPhraseText( phrase ):

	length = len(phrase["words"])
		
	out = ""
	for i in range( 0, length ):
		if re.match( '[a-zA-Z0-9]', phrase["words"][i]):
			if i > 0:
				out += " " + phrase["words"][i]
			else:
				out += phrase["words"][i]
		else:
			out += phrase["words"][i]
			
	return out
	

			

	


	
	