#!/usr/bin/env python
#		            Script Python
#------------------------------------------------------
# valideSiteLog.py verifie la conformite des sites log
#------------------------------------------------------
# rinexheadermaker.py adaptation de valideSiteLog.py
# Author : C. Bouche
# Date   : Juin 2012
#------------------------------------------------------
# Ecriture d'un fichier de conf pour teqc
# En entree :
# 	>	site.log d'une station
#	>	date de l'observation
#	>	nom du fichier de sortie (facultatif)
# En sortie :
# 	<	site.log.cfg pour teqc
#------------------------------------------------------
# Le fichier de conf permet de completer le Rinex
#		context
#			-agence, operateur
#       information sur le monument
#			-nom, hauteur d'instrument
#       systeme GPS
#			-G (GPS), R (GLONASS), M (GSP+GLONASS)
#       position aproximative
#			-X, Y, Z wgs84
#       recepteur installe a la date d
#			-type, numero de serie, versHard
#       antenne installe a la date d
#       	-type, numero de serie
#------------------------------------------------------

import getopt
import os
import re
import sys


def usage():
	print ("rinexheadermaker.py -f SITELOGFILE -d yyyy/mm/jj [-o output.cfgfiles]")

def parseArgs(arguments):
	try:
		opts, args = getopt.getopt(arguments, "hf:d:o:", ["help", "file=", "date=", "output="])
	except getopt.GetoptError, err:
		print str(err)
		usage()
		sys.exit(2)
	siteLog = None
	date = None
	cfgname = ""
	for o, a in opts:
		if o in ("-h", "--help"):
			usage()
			sys.exit()
		elif o in ("-f", "--file"):
			siteLog = a
		elif o in ("-d", "--date"):
			date = a
		elif o in ("-o", "--output"):
			cfgname = a
		else:
			assert False, "unhandled option"
	if siteLog == None:
		usage()
		sys.exit()
	else:
		return siteLog, date, cfgname

# nom du fichier log, date d'obs
siteLogName, date, cfgname = parseArgs(sys.argv[1:])
# annee, mois, jour de l'obs
year, month, day = date.split("/")[0], date.split("/")[1], date.split("/")[2]

##Fonction permettant de remonter au debut de la section.

def searchSection(lines,line):
        flag = False
        expectedLine ='^[0-9]{1,2}\.[x0-9]{1,2} .*(\n|\r\n?)$'
        regexp = re.compile(expectedLine)
        while flag == False:
                resultat = regexp.search(lines[line])
                if not resultat : line+=1
                else : flag = True
        return line

##Fonction permettant de retrouver en REMONTANT la ligne de debut de commentaires de 
##chaque section afin d'en deduire le nombre de sous-sections
##(prealable de la fonction controleNumeroSection)

##Entrees  : -lines : correspondant a linesCleaned (le fichier purge des espaces)
##           -line : ligne a partir de laquelle on commence a "remonter"
##           -numSection : numero de la section. Important car la ligne de commentaires
##                         differe selon les sections ("Additional Information/ Notes ...)

##Sortie : ligne correspondant au debut des commentaires

def searchComment(lines,line,numSection):
        flag = False
        if numSection == 1 :
                expectedLine ='^     Additional Information   : .*(\n|\r\n?)$'
        elif numSection == 85 :
                expectedLine ='^8.5.[0-9] Other Instrumentation  : .*(\n|\r\n?)$'
        elif numSection ==91 :
                expectedLine ='       Additional Information : .*(\n|\r\n?)$'
        else :  expectedLine ='^       Notes                  : .*(\n|\r\n?)$'
        
        regexp = re.compile(expectedLine)
        while flag == False:
                resultat = regexp.search(lines[line])
                if not resultat : line-=1
                else : flag = True
        return line

##Fonction controlant les numeros des sous-sections (doublons + ordre croissant)
##Comparaison a une liste "sousSections" cree comprenant l'emsemble des numeros
##des sous-sections.
##sousSections est cree a partir du num max que l'on deduit comme etant la section
##situee juste avant de celle en .x

##Entrees : line = ligne de debut de section
##             i = numero de la section (important de le preciser car chaque section
##                 ne possede pas le meme nombre de lignes

##Sortie : numeroSectionFinale = nombre de sous-sections permettant d'en deduire le
##                               le nombre d'iterations necessaires.
        
def controleNumeroSection(line,i):
	debut = line
        flagSectionVide = False
        istr = str(i)
        if i != 8 and i!=9 and i != 81 and i != 82 and i != 83 and i != 84 and i != 85 and i!=91 and i!=92 and i!=93:
                while not linesCleaned[line].startswith(istr+".x"): line+=1
                if i == 3:                  
                        commentLine = searchComment(linesCleaned,line,1)
                        lineMaxi=commentLine - 8
                        if not linesCleaned[lineMaxi].startswith("3."):
                                print 'Section 3 vide'
                                flagSectionVide = True
                                line+=9
                                debut+=9
                elif i==4 :
                        commentLine = searchComment(linesCleaned,line,1)
                        lineMaxi = commentLine-13
                        if not linesCleaned[lineMaxi].startswith("4."):
                                print 'Section 4 vide'
                                flagSectionVide = True
                                line+=14
                                debut+=14
                
                elif i == 5 :
                        commentLine = searchComment(linesCleaned,line,1)
                        lineMaxi = commentLine-11
                        if not linesCleaned[lineMaxi].startswith("5."):
                                print 'Section 5 vide'
                                flagSectionVide = True
                                line+=13
                                debut+=13
                        
                elif i == 6 :
                        commentLine = searchComment(linesCleaned,line,6)
                        lineMaxi = commentLine-3
                        if not linesCleaned[lineMaxi].startswith("6."):
                                print 'Section 6 vide'
                                flagSectionVide = True
                                line+=5
                                debut+=5
                                numeroSectionFinale = 0

                elif i == 7 : 
                        commentLine = searchComment(linesCleaned,line,7)
                        lineMaxi = commentLine-3
                        if not linesCleaned[lineMaxi].startswith("7."):
                                print 'Section 7 vide'
                                flagSectionVide = True
                                line+=5
                                debut+=5
                                
                elif i == 10 : 
                        lineMaxi = line-2
                        if not linesCleaned[lineMaxi].startswith("10."):
                                print 'Section 10 vide'
                                flagSectionVide = True
                                line+=2
                                debut+=2
                
                if not flagSectionVide :
                        ligneNumeroSection= linesCleaned[lineMaxi]
			matchObj = re.match( r'([0-9]+)\.([0-9]+) .*', ligneNumeroSection, re.M|re.I)
			numeroSectionFinale = 1
			if matchObj:
				numeroSectionFinale = int(matchObj.group(2))
                        sousSections = range(1,numeroSectionFinale+1)
                        section = linesCleaned[debut]
                        while sousSections != []:
				numSection = None
				matchObj = re.match( r'([0-9]+)\.([0-9]+) .*', section, re.M|re.I)
				if matchObj:
					numSection = int(matchObj.group(2))
                                if numSection == sousSections[0] :
                                        print "Section "+ istr+"."+str(numSection)+" ok"
                                        del sousSections[0]
                                        debut=searchSection(linesCleaned,debut+1)
                                        section = linesCleaned[debut]
                                else :
                                        print " La section "+ istr+"."+ str(numSection)+" n est pas correctement numerotee"
                                        os.system("pause")
                                        sys.exit(2)
                                        
                return numeroSectionFinale

        else :
                while not linesCleaned[line].startswith(istr[0]+"."+istr[1]+".x"): line+=1
                if istr == '81' :
                        commentLine = searchComment(linesCleaned,line,8)
                        lineMaxi = commentLine-9
                        if not linesCleaned[lineMaxi].startswith("8.1."):                 
                                print 'Section 8.1 vide'
                                flagSectionVide = True
                                line+=10
                                debut+=10
                                
                elif istr == '82' :
                        commentLine = searchComment(linesCleaned,line,8)
                        lineMaxi = commentLine-8
                        if not linesCleaned[lineMaxi].startswith("8.2."):                 
                                print 'Section 8.2 vide'
                                flagSectionVide = True
                                line+=9
                                debut+=9
                                
                elif istr == '83' :
                        commentLine = searchComment(linesCleaned,line,8)
                        lineMaxi = commentLine-9
                        if not linesCleaned[lineMaxi].startswith("8.3."):                 
                                print 'Section 8.3 vide'
                                flagSectionVide = True
                                line+=10
                                debut+=10
                                
                elif istr == '84' :                      
                        commentLine = searchComment(linesCleaned,line,8)                    
                        lineMaxi = commentLine-7                       
                        if not linesCleaned[lineMaxi].startswith("8.4."):                 
                                print 'Section 8.4 vide'
                                flagSectionVide = True
                                line+=8
                                debut+=8

                elif istr == '85' :
                        commentLine = searchComment(linesCleaned,line,85)
                        lineMaxi = commentLine
                        if not linesCleaned[lineMaxi].startswith("8.5."):                 
                                print 'Section 8.5 vide'
                                flagSectionVide = True
                                line+=2
                                debut+=2

                elif istr == '91' :
                        commentLine = searchComment(linesCleaned,line,91)
                        lineMaxi = commentLine-3
                        if not linesCleaned[lineMaxi].startswith("9.1."):                 
                                print 'Section 9.1 vide'
                                flagSectionVide = True
                                line+=4
                                debut+=4

                elif istr == '92' or istr == '93' :
                        commentLine = searchComment(linesCleaned,line,91)
                        lineMaxi = commentLine-2
                        if not linesCleaned[lineMaxi].startswith("9."+istr[1]+"."):                 
                                print 'Section 9.'+istr[1]+'vide'
                                flagSectionVide = True
                                line+=3
                                debut+=3
                      
                if not flagSectionVide :
                        ligneNumeroSection= linesCleaned[lineMaxi]
                        print ligneNumeroSection
                        numeroSectionFinale = int(ligneNumeroSection[4])
                        sousSections = range(1,numeroSectionFinale+1)
                        section = linesCleaned[debut]
                        while sousSections != []:
                                compteur =1 
                                numSection = int(section[4])
                                if numSection == sousSections[0] :
                                        print "Section "+ istr[0]+"."+ istr[1]+"."+str(compteur)+ " ok  "
                                        del sousSections[0]
                                        debut=searchSection(linesCleaned,debut+1)
                                        section = linesCleaned[debut]
                                else :
                                        print " La section "+ istr[0]+"."+ str(numSection)+"."+istr[1]+ " n est pas correctement numerotee"
                                        os.system("pause")
                                        sys.exit(2)
                                compteur+=1
                                
                return numeroSectionFinale

##Verification des commentaires (plusieurs lignes + ne depassent pas 80 en colonnes)
##Sortie : begin = correspond a la ligne suivante de la fin des commentaires
def parseComment(lines,begin,numSection):
	debutComment = begin
	if numSection == 100 :
                expectedInfo ='^         Distance/activity    : .{0,47}(\n|\r\n?)$'
	elif numSection == 1 or numSection==130 :
                expectedInfo ='^     Additional Information   : .{0,47}(\n|\r\n?)$'
	elif numSection == 91 :
                expectedInfo ='^       Additional Information : .{0,47}(\n|\r\n?)$'
        elif numSection == 85 :
                expectedInfo ='^8.5.[0-9] Other Instrumentation  : .{0,47}(\n|\r\n?)$'
        elif numSection == 111 :
                expectedInfo ='     Agency                   : .{0,47}(\n|\r\n?)$'
        elif numSection == 112 :
                expectedInfo ='     Mailing Address          : .{0,47}(\n|\r\n?)$'
        else :  expectedInfo ='^       Notes                  : .{0,47}(\n|\r\n?)$'
	regexp = re.compile(expectedInfo)
	resultat = regexp.search(lines[debutComment])
	if not resultat:
		print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (debutComment,expectedInfo,lines[debutComment]))
		sys.exit()
	debutComment+=1
	if numSection <100 :
                expectedTest = '^[0-9].[x0-9]?.*(\n|\r\n?)$'
                regexp = re.compile(expectedTest)
                resultat=regexp.search(lines[debutComment])
                begin+=1
        elif numSection ==100:
                expectedTest ='^     Additional Information   :.*(\n|\r\n?)$'
                regexp = re.compile(expectedTest)
                resultat=regexp.search(lines[debutComment])
                begin+=1
        elif numSection ==111:
                expectedTest ='^     Preferred Abbreviation   :.*(\n|\r\n?)$'
                regexp = re.compile(expectedTest)
                resultat=regexp.search(lines[debutComment])
                begin+=1
        elif numSection ==112:
                expectedTest ='^     Primary Contact$'
                regexp = re.compile(expectedTest)
                resultat=regexp.search(lines[debutComment])
                begin+=1
        elif numSection ==130:
                expectedTest ='^     Antenna Graphics with Dimensions$'
                regexp = re.compile(expectedTest)
                resultat=regexp.search(lines[debutComment])
                begin+=1
                
        if not resultat :
                flag = False
                if numSection <100: 
                        expectedSection ='^[0-9]{1,2}.([x0-9])*.*(\n|\r\n?)$'
                elif numSection == 100:
                        expectedSection ='^     Additional Information   :.*(\n|\r\n?)$'
                elif numSection == 111:
                        expectedSection ='^     Preferred Abbreviation   :.*(\n|\r\n?)$'
                elif numSection == 112:
                        expectedSection ='^     Primary Contact$'
                elif numSection ==113:
                        expectedTest ='^     Antenna Graphics with Dimensions$'
                
                regexp = re.compile(expectedSection)
                while flag == False:
                        resultat = regexp.search(lines[begin])
                        if not resultat : begin+=1
                        else : flag = True        
                finComment = begin
                for i in range(finComment-debutComment):
                        expectedComment = ['^                              : .{0,47}(\n|\r\n?)$']
                        regexp = re.compile(expectedComment[0])
                        resultat = regexp.search(lines[debutComment +i])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (debutComment +i,expectedComment[0],lines[debutComment +i]))
                                sys.exit()
                print "Commentaires ok"

        return begin

## HEADER
#     XXXX Site Information Form (site log)
#     International GNSS Service
#     See Instructions at:
#       ftp://igscb.jpl.nasa.gov/pub/station/general/sitelog_instr.txt
def parseHeader(lines,begin):
	#print('Parsing Header')
	expected = [
		'^     [A-Z0-9]{4} Site Information Form( \(site log\))?(\n|\r\n?)$',
		'^     (.*)(\n|\r\n?)$',
		'^     See Instructions at:(\n|\r\n?)$',
		'^       ftp://igscb.jpl.nasa.gov/pub/station/general/sitelog_instr.txt(\n|\r\n?)$',
		]
	for i in range(len(expected)):
		regexp = re.compile(expected[i])
		resultat = regexp.search(lines[i+begin])
		if not resultat:
			print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
			sys.exit()
	return begin + len(expected)

## FORM
#0.   Form
#     Prepared by (full name)  : 
#     Date Prepared            : (CCYY-MM-DD)
#     Report Type              : (NEW/UPDATE)
#     If Update:
#      Previous Site Log       : (ssss_ccyymmdd.log)
#      Modified/Added Sections : (n.n,n.n,...)
def parseForm(lines,begin):
	#print('Parsing Form')
	expected = [
		'^0\.   Form(\n|\r\n?)$',
		'^     Prepared by \(full name\)  : .+(\n|\r\n?)$',
		'^     Date Prepared            : [0-9]{4}-[0-9]{2}-[0-9]{2}(\n|\r\n?)$',
		'^     Report Type              : (NEW|UPDATE)(\n|\r\n?)$',
		'^     If Update:(\n|\r\n?)$',
		'^      Previous Site Log       : ([a-z0-9]{4}_[0-9]{8}.log)?(\n|\r\n?)$',
		'^      Modified/Added Sections : ([0-9]+\.[0-9]+\.?[0-9]*,?)*(\n|\r\n?)$',
		]
	for i in range(7):
                regexp = re.compile(expected[i])
                resultat = regexp.search(lines[i+begin])
                if not resultat:
                        print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                        sys.exit()
        return begin + 7

## SITE ID
#1.   Site Identification of the GNSS Monument
#     Site Name                : 
#     Four Character ID        : (A4)
#     Monument Inscription     : 
#     IERS DOMES Number        : (A9)
#     CDP Number               : (A4)
#     Monument Description     : (PILLAR/BRASS PLATE/STEEL MAST/etc)
#       Height of the Monument : (m)
#       Monument Foundation    : (STEEL RODS, CONCRETE BLOCK, ROOF, etc)
#       Foundation Depth       : (m)
#     Marker Description       : (CHISELLED CROSS/DIVOT/BRASS NAIL/etc)
#     Date Installed           : (CCYY-MM-DDThh:mmZ)
#     Geologic Characteristic  : (BEDROCK/CLAY/CONGLOMERATE/GRAVEL/SAND/etc)
#       Bedrock Type           : (IGNEOUS/METAMORPHIC/SEDIMENTARY)
#       Bedrock Condition      : (FRESH/JOINTED/WEATHERED)
#       Fracture Spacing       : (1-10 cm/11-50 cm/51-200 cm/over 200 cm)
#       Fault zones nearby     : (YES/NO/Name of the zone)
#         Distance/activity    : (multiple lines)
#     Additional Information   : (multiple lines)
def parseSiteID(lines,begin):
	#print('Parsing Site ID')
	expected = [
		'^1\.   Site Identification of the GNSS Monument(\n|\r\n?)$',
		'^     Site Name                : .*(\n|\r\n?)$',
		'^     Four Character ID        : [A-Z0-9]{4}(\n|\r\n?)$',
		'^     Monument Inscription     : .*(\n|\r\n?)$',
		'^     IERS DOMES Number        : [A-Z0-9]{9}(\n|\r\n?)$',
		'^     CDP Number               : [A-Z0-9]{4}(\n|\r\n?)$',
		'^     Monument Description     : .*(\n|\r\n?)$',
		'^       Height of the Monument : ([0-9]+\.?[0-9]*)? m(\n|\r\n?)$',
		'^       Monument Foundation    : .*(\n|\r\n?)$',
		'^       Foundation Depth       : ([0-9]+\.?[0-9]*)? m(\n|\r\n?)$',
		'^     Marker Description       : .*(\n|\r\n?)$',
		'^     Date Installed           : [0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}Z)?(\n|\r\n?)$',
		'^     Geologic Characteristic  : .*(\n|\r\n?)$',
		'^       Bedrock Type           : (IGNEOUS|METAMORPHIC|SEDIMENTARY|BASALTIC)?(\n|\r\n?)$',
		'^       Bedrock Condition      : (FRESH|JOINTED|WEATHERED)?(\n|\r\n?)$',
		'^       Fracture Spacing       : (0 cm|1-10 cm|11-50 cm|51-200 cm|over 200 cm)?(\n|\r\n?)$',
		'^       Fault zones nearby     : .*(\n|\r\n?)$',
#		'^         Distance/activity    : .*(\n|\r\n?)$',
		]
	for i in range(len(expected)):
		regexp = re.compile(expected[i])
		resultat = regexp.search(lines[i+begin])
		if not resultat:
			print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
			sys.exit()
		else:
			if int(i) == 2:
				Monument4ID = lines[i+begin].split(": ")[1]
				Monument4ID = Monument4ID.rstrip()
				rinexheader_addline("-O.mo[nument]", Monument4ID)
#			if int(i) == 7:
#				MonumentHeight = lines[i+begin].split(": ")[1]
#				MonumentHeight = MonumentHeight.rstrip()
#				hEN_m = ""
#				hEN_m += MonumentHeight
#				hEN_m += " 0.0000 0.0000"
#				rinexheader_addline("-O.pe[hEN,m]", hEN_m)
	begin = begin +len(expected)
	begin = parseComment(lines,begin,100)
	begin = parseComment(lines,begin,1)
	return begin

## START SITE LOC SECTION
#2.   Site Location Information
def startSiteLoc(line):
	#print('Parsing Site Location Information Header')
	expected = '^2\.   Site Location Information(\n|\r\n?)$'
	regexp = re.compile(expected)
	resultat = regexp.search(line)
	if not resultat:
		print('Erreur sur la ligne.\n "%s" Attendu.\n "%s" Trouve' % (expected,line))
		sys.exit()
## SITE LOC
#2.   Site Location Information
#     City or Town             : 
#     State or Province        : 
#     Country                  : 
#     Tectonic Plate           : 
#     Approximate Position (ITRF)
#       X coordinate (m)       : 
#       Y coordinate (m)       : 
#       Z coordinate (m)       : 
#       Latitude (N is +)      : (+/-DDMMSS.SS)
#       Longitude (E is +)     : (+/-DDDMMSS.SS)
#       Elevation (m,ellips.)  : (F7.1)
#     Additional Information   : (multiple lines)
def parseSiteLoc(lines,begin):
	#print('Parsing Site Location')
	expected = [
		'^2\.   Site Location Information(\n|\r\n?)$',
		'^     City or Town             : .+(\n|\r\n?)$',
		'^     State or Province        : .+(\n|\r\n?)$',
		'^     Country                  : .+(\n|\r\n?)$',
		'^     Tectonic Plate           : .+(\n|\r\n?)$',
		'^     Approximate Position \(ITRF\)(\n|\r\n?)$',
		'^       X coordinate \(m\)       : (\+|-)?[0-9]+.[0-9]+(\n|\r\n?)$',
		'^       Y coordinate \(m\)       : (\+|-)?[0-9]+.[0-9]+(\n|\r\n?)$',
		'^       Z coordinate \(m\)       : (\+|-)?[0-9]+.[0-9]+(\n|\r\n?)$',
		'^       Latitude \(N is \+\)      : (\+|-)[0-9]{6}\.[0-9]{2}(\n|\r\n?)$',
		'^       Longitude \(E is \+\)     : (\+|-)[0-9]{7}\.[0-9]{2}(\n|\r\n?)$',
		'^       Elevation \(m,ellips\.\)  : (\+|-)?[0-9]{5}(\.[0-9])?(\n|\r\n?)$',
		]
	Wgs84Coordinates = ""
	for i in range(len(expected)):
		regexp = re.compile(expected[i])
		resultat = regexp.search(lines[i+begin])
		if not resultat:
			print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
			sys.exit()
		else:
			if int(i) == 6:
				Xcoord = lines[i+begin].split(": ")[1]
				Xcoord = Xcoord.rstrip()
				Wgs84Coordinates += Xcoord
			if int(i) == 7:
				Ycoord = lines[i+begin].split(":")[1]
				Ycoord = Ycoord.rstrip()
				Wgs84Coordinates += Ycoord
			if int(i) == 8:
				Zcoord = lines[i+begin].split(":")[1]
				Zcoord = Zcoord.rstrip()
				Wgs84Coordinates += Zcoord
	rinexheader_addline("-O.px[WGS84xyz,m]", Wgs84Coordinates)
	begin = begin +len(expected)
	begin = parseComment(lines,begin,1)
	return begin

## START RECEIVER SECTION
#3.   GNSS Receiver Information
def startReceiver(line):
	#print('Parsing Receiver Information Header')
	expected = '^3\.   GNSS Receiver Information(\n|\r\n?)$'
	regexp = re.compile(expected)
	resultat = regexp.search(line)
	if not resultat:
		print('Erreur sur la ligne.\n "%s" Attendu.\n "%s" Trouve' % (expected,line))
		sys.exit()

## RECEIVER INFO
#3.1  Receiver Type            : (A20, from rcvr_ant.tab; see instructions)
#     Satellite System         : (GPS/GLONASS/GPS+GLONASS)
#     Serial Number            : (A20, but note the first A5 is used in SINEX)
#     Firmware Version         : (A11)
#     Elevation Cutoff Setting : (deg)
#     Date Installed           : (CCYY-MM-DDThh:mmZ)
#     Date Removed             : (CCYY-MM-DDThh:mmZ)
#     Temperature Stabiliz.    : (none or tolerance in degrees C)
#     Additional Information   : (multiple lines)
def parseReceiver(lines,begin):
	numSection = controleNumeroSection(begin,3)
	for i in range(1,numSection+1):
		#print('Parsing Receiver Information %s' % (lines[begin]))
		expected = [
			'^3\.([0-9] |[0-9]{2}) Receiver Type            : (LEICA GR25|TPS GB-1000|TRIMBLE NETRS|TRIMBLE NETR9|TRIMBLE ALLOY|ASHTECH Z-X|ASHTECH UZ-12|ASHTECH Z-XII3|SPECTRA SP90M)(\n|\r\n?)$',
			'^     Satellite System         : (GPS|GLO|GPS\+GLO|GPS\+GLO\+GAL|GPS\+GLO\+GAL\+BDS\+QZSS\+SBAS)(\n|\r\n?)$',
			'^     Serial Number            : .*(\n|\r\n?)$',
			'^     Firmware Version         : .*(\n|\r\n?)$',
			'^     Elevation Cutoff Setting : [0-9]*(\n|\r\n?)$',
			'^     Date Installed           : [0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}Z)?(\n|\r\n?)$',
			'^     Date Removed             : ([0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}Z)?)|(\(CCYY-MM-DDThh:mmZ\))(\n|\r\n?)$',
			'^     Temperature Stabiliz\.    : ([0-9]*|NONE)(\n|\r\n?)$',
			]
		for i in range(len(expected)):
			regexp = re.compile(expected[i])
			resultat = regexp.search(lines[i+begin])
			if not resultat:
				print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
				sys.exit()
			else:
				if int(i) == 0:
					ReceiverTypeFound = lines[i+begin].split(": ")[1]
					ReceiverTypeFound = ReceiverTypeFound.rstrip()
					comment = "----------------Receiver "
					comment += ReceiverTypeFound
					comment += "----------------------"
					rinexheader_addline("+O.c[omment]", comment)
				if int(i) == 1:
					SatelliteSystem = lines[i+begin].split(": ")[1]
					SatelliteSystem = SatelliteSystem.rstrip()
				if int(i) == 2:
					ReceiverSerialFound = lines[i+begin].split(": ")[1]
					ReceiverSerialFound = ReceiverSerialFound.rstrip()
				if int(i) == 3:
					FirmwareVersion = lines[i+begin].split(": ")[1]
					FirmwareVersion = FirmwareVersion.rstrip()
				if int(i) == 5:
					Installed = "---------------Installed on  "
					data = lines[i+begin].split(":")[1]
					data = data.rstrip()
					data = data.split("T")[0]
					Installed += data
					Installed += "---------------------"
					rinexheader_addline("+O.c[omment]", Installed)
					# on test si le recepteur est bien installe a la date d
					yearInstal, monthInstal, dayInstal = data.split("-")[0], data.split("-")[1], data.split("-")[2]
					if (float(year) > float(yearInstal)):
						bool_instal = 1
					else:
						if(float(year) == float(yearInstal) and float(month) > float(monthInstal)):
							bool_instal = 1
						else:
							if(float(year) == float(yearInstal) and float(month) == float(monthInstal) and float(day) > float(dayInstal)):
								bool_instal = 1
							else:
								bool_instal = 0
				if int(i) == 6:
					data = lines[i+begin].split(": ")[1]
					data = data.rstrip()
					if data == "(CCYY-MM-DDThh:mmZ)":
						data = ""
					Removed = "---------------Removed   on  "
					data = data.split("T")[0]
					Removed += data
					Removed += "---------------------"
					rinexheader_addline("+O.c[omment]", Removed)
					# si la date d'installation est coherente
					if bool_instal == 1:
						# on test si le recepteur n'est pas retire a la date d
						if data == "":
							bool_remove = 0
						else:
							yearRemove, monthRemove, dayRemove = data.split("-")[0], data.split("-")[1], data.split("-")[2]
							if (float(year) < float(yearRemove)):
								bool_remove = 0
							else:
								if(float(year) == float(yearRemove) and float(month) < float(monthRemove)):
									bool_remove = 0
								else:
									if(float(year) == float(yearRemove) and float(month) == float(monthRemove) and float(day) < float(dayRemove)):
										bool_remove = 0
									else:
										bool_remove = 1
						if bool_remove == 0:
							rinexheader_addline("-O.rt", ReceiverTypeFound)
							if SatelliteSystem == "GPS":
								rinexheader_addline("-O.s[ystem]", "G")
							elif SatelliteSystem == "GPS+GLO":
								rinexheader_addline("-O.s[ystem]", "M")
							elif SatelliteSystem == "GLO":
								rinexheader_addline("-O.s[ystem]", "R")			
							rinexheader_addline("-O.rn", ReceiverSerialFound)
							rinexheader_addline("-O.rv", FirmwareVersion)
		begin = begin + len(expected)
		begin = parseComment(lines,begin,1)
	return begin

## START ANTENNA SECTION
#4.   GNSS Antenna Information
def startAntenna(line):
	#print('Parsing Antenna Information Header')
	expected = '^4\.   GNSS Antenna Information(\n|\r\n?)$'
	regexp = re.compile(expected)
	resultat = regexp.search(line)
	if not resultat:
		print('Erreur sur la ligne.\n "%s" Attendu.\n "%s" Trouve' % (expected,line))
		sys.exit()

## ANTENNA INFO
#4.1  Antenna Type             : (A20, from rcvr_ant.tab; see instructions)
#     Serial Number            : (A*, but note the first A5 is used in SINEX)
#     Antenna Reference Point  : (BPA/BCR/XXX from "antenna.gra"; see instr.)
#     Marker->ARP Up Ecc. (m)  : (F8.4)
#     Marker->ARP North Ecc(m) : (F8.4)
#     Marker->ARP East Ecc(m)  : (F8.4)
#     Alignment from True N    : (deg; + is clockwise/east)
#     Antenna Radome Type      : (A4 from rcvr_ant.tab; see instructions)
#     Radome Serial Number     :
#     Antenna Cable Type       : (vendor & type number)
#     Antenna Cable Length     : (m)
#     Date Installed           : (CCYY-MM-DDThh:mmZ)
#     Date Removed             : (CCYY-MM-DDThh:mmZ)
#     Additional Information   : (multiple lines)
def parseAntenna(lines,begin):
	numSection = controleNumeroSection(begin,4)
	for i in range(1,numSection+1):
		#print('Parsing Antenna Information %s' % (lines[begin]))
		expected = [
			'^4\.([0-9] |[0-9]{2}) Antenna Type             : (TPSPG_A1(_6)?(\+GP)?|TRM41249\.00|ASH700936A|ASH700228D|ASH700936E|ASH700936E_C|ASH701975\.01A(GP)?|ASH700700\.A|ASH700700\.C|ASH701945C_M|TRM57971\.00|TRM55971\.00|TRM115000\.00|LEIAS10|LEIAR10|AERAT1675_120)[ ]*([A-Z]{4}?)(\n|\r\n?)$',
			'^     Serial Number            : .*(\n|\r\n?)$',
			'^     Antenna Reference Point  : .*(\n|\r\n?)$',
			'^     Marker->ARP Up Ecc\. \(m\)  : [0-9]{3}\.[0-9]{4}(\n|\r\n?)$',
			'^     Marker->ARP North Ecc\(m\) : [0-9]{3}\.[0-9]{4}(\n|\r\n?)$',
			'^     Marker->ARP East Ecc\(m\)  : [0-9]{3}\.[0-9]{4}(\n|\r\n?)$',
			'^     Alignment from True N    : [0-9]+(\n|\r\n?)$',
			'^     Antenna Radome Type      : [0-9A-Z]{4}(\n|\r\n?)$',
			'^     Radome Serial Number     : .*(\n|\r\n?)$',
			'^     Antenna Cable Type       : .*(\n|\r\n?)$',
			'^     Antenna Cable Length     : ([0-9]*\.?[0-9]*) m(\n|\r\n?)$',
			'^     Date Installed           : [0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}Z)?(\n|\r\n?)$',
			'^     Date Removed             : ([0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}Z)?)|(\(CCYY-MM-DDThh:mmZ\))(\n|\r\n?)$',
			]
		for i in range(len(expected)):
			regexp = re.compile(expected[i])
			resultat = regexp.search(lines[i+begin])
			if not resultat:
				print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
				sys.exit()
			else:
				if int(i) == 0:
					AntennaTypeFound = lines[i+begin].split(": ")[1]
					AntennaTypeFound = AntennaTypeFound.rstrip()
					comment = "--------------Antenna "
					comment += AntennaTypeFound
					comment += "-----------------------"
					rinexheader_addline("+O.c[omment]", comment)
				if int(i) == 1:
					AntennaSerialFound = lines[i+begin].split(": ")[1]
					AntennaSerialFound = AntennaSerialFound.rstrip()
				if int(i) == 3:
					AntennaCorrection = lines[i+begin].split(": ")[1]
					AntennaCorrection = AntennaCorrection.rstrip()
					hEN_m = ""
					hEN_m += AntennaCorrection
				if int(i) == 4:
					AntennaCorrection = lines[i+begin].split(": ")[1]
					AntennaCorrection = AntennaCorrection.rstrip()
					hEN_m += " "
					hEN_m += AntennaCorrection
				if int(i) == 5:
					AntennaCorrection = lines[i+begin].split(": ")[1]
					AntennaCorrection = AntennaCorrection.rstrip()
					hEN_m += " "
					hEN_m += AntennaCorrection
					rinexheader_addline("-O.pe[hEN,m]", hEN_m)
				if int(i) == 11:
					Installed = "---------------Installed on  "
					data = lines[i+begin].split(": ")[1]
					data = data.rstrip()
					data = data.split("T")[0]
					Installed += data
					Installed += "---------------------"
					rinexheader_addline("+O.c[omment]", Installed)
					# on test si le recepteur est bien installe a la date d
					yearInstal, monthInstal, dayInstal = data.split("-")[0], data.split("-")[1], data.split("-")[2]
					if (float(year) > float(yearInstal)):
						bool_instal = 1
					else:
						if(float(year) == float(yearInstal) and float(month) > float(monthInstal)):
							bool_instal = 1
						else:
							if(float(year) == float(yearInstal) and float(month) == float(monthInstal) and float(day) > float(dayInstal)):
								bool_instal = 1
							else:
								bool_instal = 0
				if int(i) == 12:
					data = lines[i+begin].split(": ")[1]
					data = data.rstrip()
					if data == "(CCYY-MM-DDThh:mmZ)":
						data = ""
					Removed = "---------------Removed   on  "
					data = data.split("T")[0]
					Removed += data
					Removed += "---------------------"
					rinexheader_addline("+O.c[omment]", Removed)
					# si la date d'installation est coherente
					if bool_instal == 1:
						# on test si le recepteur n'est pas retire a la date d
						if data == "":
							bool_remove = 0
						else:
							yearRemove, monthRemove, dayRemove = data.split("-")[0], data.split("-")[1], data.split("-")[2]
							if (float(year) < float(yearRemove)):
								bool_remove = 0
							else:
								if(float(year) == float(yearRemove) and float(month) < float(monthRemove)):
									bool_remove = 0
								else:
									if(float(year) == float(yearRemove) and float(month) == float(monthRemove) and float(day) < float(dayRemove)):
										bool_remove = 0
									else:
										bool_remove = 1
						if bool_remove == 0:
							rinexheader_addline("-O.at", AntennaTypeFound)
							rinexheader_addline("-O.an", AntennaSerialFound)
		begin = begin + len(expected)
		begin = parseComment(lines,begin,1)
	return begin

## SITE INFO
##5.   Surveyed Local Ties
##5.1  Tied Marker Name         : 
##     Tied Marker Usage        : (SLR/VLBI/LOCAL CONTROL/FOOTPRINT/etc)
##     Tied Marker CDP Number   : (A4)
##     Tied Marker DOMES Number : (A9)
##     Differential Components from GNSS Marker to the tied monument (ITRS)
##       dx (m)                 : (m)
##       dy (m)                 : (m)
##       dz (m)                 : (m)
##     Accuracy (mm)            : (mm)
##     Survey method            : (GPS CAMPAIGN/TRILATERATION/TRIANGULATION/etc)
##     Date Measured            : (CCYY-MM-DDThh:mmZ)
##     Additional Information   : (multiple lines)

def parseSite(lines,begin):
        numSection = controleNumeroSection(begin,5)
        for i in range(1,numSection+1):
                print('Parsing Site Information')
                expected = [
                        '^5\.([0-9] |[0-9]{2}) Tied Marker Name         : .*(\n|\r\n?)$',         
                        '^     Tied Marker Usage        : .*(\n|\r\n?)$',
                        '^     Tied Marker CDP Number   : ([A-Z0-9]{4})?(\n|\r\n?)$',
                        '^     Tied Marker DOMES Number : ([A-Z0-9]{9})?(\n|\r\n?)$',
                        '^     Differential Components from GNSS Marker to the tied monument \(ITRS\)',
                        '^       dx \(m\)                 : (\+|-)?[0-9]+\.[0-9]{4}(\n|\r\n?)$',
                        '^       dy \(m\)                 : (\+|-)?[0-9]+\.[0-9]{4}(\n|\r\n?)$',
                        '^       dz \(m\)                 : (\+|-)?[0-9]+\.[0-9]{4}(\n|\r\n?)$',
                        '^     Accuracy \(mm\)            : \+-[0-9]+\.[0-9](\n|\r\n?)$',
                        '^     Survey method            : .*(\n|\r\n?)$',
                        '^     Date Measured            : ([0-9]{4}-[0-9]{2}-[0-9]{2}(T[0-9]{2}:[0-9]{2}Z)?)|(\(CCYY-MM-DDThh:mmZ\))(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,1)
	return begin
	
## FREQUENCY INFO
##6.   Frequency Standard
##6.1  Standard Type            : (INTERNAL or EXTERNAL H-MASER/CESIUM/etc)
##       Input Frequency        : (if external)
##       Effective Dates        : (CCYY-MM-DD/CCYY-MM-DD)
##       Notes                  : (multiple lines)
def parseFrequence(lines,begin):
        numSection = controleNumeroSection(begin,6)
        for i in range(1,numSection+1):
                print('Parsing Site Frequency')
                expected = [
                        '^6\.([0-9] |[0-9]{2}) Standard Type            : .*(\n|\r\n?)$',
                        '^       Input Frequency        : .*(\n|\r\n?)$',
                        '^       Effective Dates        : [0-9]{4}-[0-9]{2}-[0-9]{2}/([0-9]{4}-[0-9]{2}-[0-9]{2}|CCYY-MM-DD)(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,6)
	return begin

## COLLOCATION INFO
##7.   Collocation Information
##7.1  Instrumentation Type     : (GPS/GLONASS/DORIS/PRARE/SLR/VLBI/TIME/etc)
##       Status                 : (PERMANENT/MOBILE)
##       Effective Dates        : (CCYY-MM-DD/CCYY-MM-DD)
##       Notes                  : (multiple lines)
def parseCollocation(lines,begin):
        numSection = controleNumeroSection(begin,7)
        for i in range(1,numSection+1):
                print('Parsing Collocation Information')
                expected = ['^7\.([0-9] |[0-9]{2}) Instrumentation Type     : .*(\n|\r\n?)$',
                        '^       Status                 : (PERMANENT|MOBILE)(\n|\r\n?)$',
                        '^       Effective Dates        : [0-9]{4}-[0-9]{2}-[0-9]{2}/([0-9]{4}-[0-9]{2}-[0-9]{2}|CCYY-MM-DD)(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,7)
	return begin

## METEO INFO
##8.   Meteorological Instrumentation
##8.1.1 Humidity Sensor Model   : 
##       Manufacturer           : 
##       Serial Number          : 
##       Data Sampling Interval : (sec)
##       Accuracy (% rel h)     : (% rel h)
##       Aspiration             : (UNASPIRATED/NATURAL/FAN/etc)
##       Height Diff to Ant     : (m)
##       Calibration date       : (CCYY-MM-DD)
##       Effective Dates        : (CCYY-MM-DD/CCYY-MM-DD)
##       Notes                  : (multiple lines)

def parseHumidity(lines,begin):
        numSection = controleNumeroSection(begin,81)
        for i in range(1,numSection+1):
                print('Humidity Sensor Model')
                expected = ['^8\.1\.([0-9] |[0-9]{2}) Humidity Sensor Model  : .*(\n|\r\n?)$',
                        '^       Manufacturer           : .*(\n|\r\n?)$',
                        '^       Serial Number          : .*(\n|\r\n?)$',
                        '^       Data Sampling Interval : [0-9](\n|\r\n?)$',
                        '^       Accuracy \(% rel h\)     : \+-[0-9]\.?[0-9]*?(\n|\r\n?)$',
                        '^       Aspiration             : .*(\n|\r\n?)$',
                        '^       Height Diff to Ant     : ([0-9]+\.[0-9])?(\n|\r\n?)$',
                        '^       Calibration date       : ([0-9]{4}-[0-9]{2}-[0-9]{2})?(\n|\r\n?)$',
                        '^       Effective Dates        : ([0-9]{4}-[0-9]{2}-[0-9]{2}/([0-9]{4}-[0-9]{2}-[0-9]{2}|CCYY-MM-DD))?(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,8)
	return begin 

## PRESSURE INFO
##8.2.1 Pressure Sensor Model   : 
##       Manufacturer           : 
##       Serial Number          : 
##       Data Sampling Interval : (sec)
##       Accuracy               : (hPa)
##       Height Diff to Ant     : (m)
##       Calibration date       : (CCYY-MM-DD)
##       Effective Dates        : (CCYY-MM-DD/CCYY-MM-DD)
##       Notes                  : (multiple lines)
	
def parsePressure(lines,begin):
        numSection = controleNumeroSection(begin,82)
        for i in range(1,numSection+1):
                print ('Pressure Sensor Model')
                expected = ['^8\.2.([0-9] |[0-9]{2}) Pressure Sensor Model  : .*(\n|\r\n?)$',
                        '^       Manufacturer           : .*(\n|\r\n?)$',
                        '^       Serial Number          : .*(\n|\r\n?)$',
                        '^       Data Sampling Interval : [0-9](\n|\r\n?)$',
                        '^       Accuracy               : \+-[0-9]+\.[0-9](\n|\r\n?)$',
                        '^       Height Diff to Ant     : [0-9]+\.[0-9](\n|\r\n?)$',
                        '^	   Calibration date       : [0-9]{4}-[0-9]{2}-[0-9]{2}(\n|\r\n?)$',
                        '^	   Effective Dates        : [0-9]{4}-[0-9]{2}-[0-9]{2}/([0-9]{4}-[0-9]{2}-[0-9]{2}|CCYY-MM-DD)(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,8)
	return begin

## TEMP INFO
##8.3.1 Temp. Sensor Model      : 
##       Manufacturer           : 
##       Serial Number          : 
##       Data Sampling Interval : (sec)
##       Accuracy               : (deg C)
##       Aspiration             : (UNASPIRATED/NATURAL/FAN/etc)
##       Height Diff to Ant     : (m)
##       Calibration date       : (CCYY-MM-DD)
##       Effective Dates        : (CCYY-MM-DD/CCYY-MM-DD)
##       Notes                  : (multiple lines)

def parseTemp(lines,begin):
        numSection = controleNumeroSection(begin,83)
        for i in range(1,numSection+1):
                print ('Temperature Sensor Model')
                expected = ['^8\.3.([0-9] |[0-9]{2}) Temp. Sensor Model     : .*(\n|\r\n?)$',
                        '^       Manufacturer           : .*(\n|\r\n?)$',
                        '^       Serial Number          : .*(\n|\r\n?)$',
                        '^       Data Sampling Interval : [0-9](\n|\r\n?)$',
                        '^       Accuracy               : \+-[0-9]+\.[0-9](\n|\r\n?)$',
                        '^       Aspiration             : .*(\n|\r\n?)$',
                        '^       Height Diff to Ant     : ([0-9]+\.[0-9])?(\n|\r\n?)$',
                        '^       Calibration date       : [0-9]{4}-[0-9]{2}-[0-9]{2}(\n|\r\n?)$',
                        '^       Effective Dates        : [0-9]{4}-[0-9]{2}-[0-9]{2}/([0-9]{4}-[0-9]{2}-[0-9]{2}|CCYY-MM-DD)(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,8)
	return begin 

## WATER VAPOR INFO
##8.4.1 Water Vapor Radiometer  : 
##       Manufacturer           : 
##       Serial Number          : 
##       Distance to Antenna    : (m)
##       Height Diff to Ant     : (m)
##       Calibration date       : (CCYY-MM-DD)
##       Effective Dates        : (CCYY-MM-DD/CCYY-MM-DD)
##       Notes                  : (multiple lines)

def parseWatorVapor(lines,begin):
        numSection = controleNumeroSection(begin,84)
        for i in range(1,numSection+1):
                print ('Water Vapor Radiometer')
                expected = ['^8\.4\.([0-9] |[0-9]{2}) Water Vapor Radiometer : .*(\n|\r\n?)$',
                        '^       Manufacturer           : .*(\n|\r\n?)$',
                        '^       Serial Number          : .*(\n|\r\n?)$',
                        '^       Distance to Antenna    : ([0-9]+\.[0-9])?(\n|\r\n?)$',
                        '^       Height Diff to Ant     : ([0-9]+\.[0-9])?(\n|\r\n?)$',
                        '^       Calibration date       : [0-9]{4}-[0-9]{2}-[0-9]{2}(\n|\r\n?)$',
                        '^       Effective Dates        : [0-9]{4}-[0-9]{2}-[0-9]{2}/([0-9]{4}-[0-9]{2}-[0-9]{2}|CCYY-MM-DD)(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,8)
	return begin

## INSTRUMENTATION INFO
##8.5.1 Other Instrumentation   : (multiple lines)
	       
def parseOtherInstru(lines,begin):
        numSection = controleNumeroSection(begin,85)
        for i in range(1,numSection+1):
                print ('Other Instrumentation')
                expected = ['^8\.5\.([0-9] |[0-9]{2}) Other Instrumentation  :.*(\n|\r\n?)$'
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin-1,85)
	return begin 

## LOCAL PERTUBATION
##9.  Local Ongoing Conditions Possibly Affecting Computed Position
##9.1.x  Radio Interferences    : (TV/CELL PHONE ANTENNA/RADAR/etc)
##       Observed Degredations  : (SN RATIO/DATA GAPS/etc)
##       Effective Dates        : (CCYY-MM-DD/CCYY-MM-DD)
##       Additional Information : (multiple lines)

def parseRadioInterferences(lines,begin):
        numSection = controleNumeroSection(begin,91)
        for i in range(1,numSection+1):
                print ('Radio Interferences')
                expected = ['^9\.1\.([0-9] |[0-9]{2}) Radio Interferences    : .*(\n|\r\n?)$',
                        '^       Observed Degradations  : .*(\n|\r\n?)$',
                        '^       Effective Dates        : [0-9]{4}-[0-9]{2}-[0-9]{2}/([0-9]{4}-[0-9]{2}-[0-9]{2}|CCYY-MM-DD)(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,91)
	return begin 




##9.2.x  Multipath Sources      : (METAL ROOF/DOME/VLBI ANTENNA/etc)
##       Effective Dates        : (CCYY-MM-DD/CCYY-MM-DD)
##       Additional Information : (multiple lines)

def parseMultipathSources(lines,begin):
        numSection = controleNumeroSection(begin,92)
        for i in range(1,numSection+1):
                print ('MultipathSources')
                expected = ['^9\.2\.([0-9] |[0-9]{2}) Multipath Sources      : .*(\n|\r\n?)$',
                        '^       Effective Dates        : [0-9]{4}-[0-9]{2}-[0-9]{2}/([0-9]{4}-[0-9]{2}-[0-9]{2}|CCYY-MM-DD)(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,91)
	return begin

##9.3.x  Signal Obstructions    : (TREES/BUILDINGS/etc)
##       Effective Dates        : (CCYY-MM-DD/CCYY-MM-DD)
##       Additional Information : (multiple lines)

def parseSignalObstructions(lines,begin):
        numSection = controleNumeroSection(begin,93)
        for i in range(1,numSection+1):
                print ('MultipathSources')
                expected = ['^9\.3\.([0-9] |[0-9]{2}) Signal Obstructions    : .*(\n|\r\n?)$',
                        '^       Effective Dates        : [0-9]{4}-[0-9]{2}-[0-9]{2}/([0-9]{4}-[0-9]{2}-[0-9]{2}|CCYY-MM-DD)(\n|\r\n?)$',
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
                begin = parseComment(lines,begin,91)
	return begin
                
##10.x Date                     : (CCYY-MM-DD/CCYY-MM-DD)
##     Event                    : (TREE CLEARING/CONSTRUCTION/etc)

def parseLocalEpisodicEffects(lines,begin):
        numSection = controleNumeroSection(begin,10)
        for i in range(1,numSection+1):
                print ('Local Episodic Effects')
                expected = ['^10\.([0-9] |[0-9]{2}) Date                     : [0-9]{4}-[0-9]{2}-[0-9]{2}/[0-9]{4}-[0-9]{2}-[0-9]{2}(\n|\r\n?)$',
                        '^     Event                    :.*(\n|\r\n?)$'
                        ]
                for i in range(len(expected)):
                        regexp = re.compile(expected[i])
                        resultat = regexp.search(lines[i+begin])
                        if not resultat:
                                print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
                                sys.exit()
                begin = begin +len(expected)
	return begin

## LOCAL AGENCY
##11.  On-Site, Point of Contact Agency Information
##     Agency                   : (multiple lines)
##     Preferred Abbreviation   : (A10)
##     Mailing Address          : (multiple lines)
##     Primary Contact
##       Contact Name           :
##       Telephone (primary)    :
##       Telephone (secondary)  :
##       Fax                    :
##       E-mail                 :
##     Secondary Contact
##       Contact Name           :
##       Telephone (primary)    :
##       Telephone (secondary)  :
##       Fax                    :
##       E-mail                 :
##     Additional Information   : (multiple lines)

def parseLocalAgency(lines,begin):
	print('Parsing Local Agency')
	expected = '^11\.  On-Site, Point of Contact Agency Information(\n|\r\n?)$'
	regexp = re.compile(expected)
	resultat = regexp.search(lines[begin])
	if not resultat:
		print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (begin,expected,lines[begin]))
		sys.exit()
	begin+=1
	begin = parseComment(lines,begin,111)
        expected ='^     Preferred Abbreviation   : .*(\n|\r\n?)$'
        regexp = re.compile(expected)
	resultat = regexp.search(lines[begin])
	if not resultat:
		print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (begin,expected,lines[begin]))
		sys.exit()
	OperatorAbbrevation = lines[begin].split(": ")[1]
	OperatorAbbrevation = OperatorAbbrevation.rstrip()
	rinexheader_addline("-O.o[perator]", OperatorAbbrevation)
	rinexheader_addline("-O.r[un_by]", OperatorAbbrevation)
	begin+=1
	begin = parseComment(lines,begin,112)
        expected = [
		'^     Primary Contact(\n|\r\n?)$',
		'^       Contact Name           : .*(\n|\r\n?)$',
		'^       Telephone \(primary\)    : .*(\n|\r\n?)$',
		'^       Telephone \(secondary\)  : .*(\n|\r\n?)$',
		'^       Fax                    : .*(\n|\r\n?)$',
		'^       E-mail                 : .*(\n|\r\n?)$',
		'^     Secondary Contact(\n|\r\n?)$',
		'^       Contact Name           : .*(\n|\r\n?)$',
		'^       Telephone \(primary\)    : .*(\n|\r\n?)$',
		'^       Telephone \(secondary\)  : .*(\n|\r\n?)$',
		'^       Fax                    : .*(\n|\r\n?)$',
		'^       E-mail                 : .*(\n|\r\n?)$',
		]
	for i in range(len(expected)):
		regexp = re.compile(expected[i])
		resultat = regexp.search(lines[i+begin])
		if not resultat:
			print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
			sys.exit()
        begin = begin +len(expected)
        begin = parseComment(lines,begin,1)
        return begin

## AGENCY
##12.  Responsible Agency (if different from 11.)
##     Agency                   : (multiple lines)
##     Preferred Abbreviation   : (A10)
##     Mailing Address          : (multiple lines)
##     Primary Contact
##       Contact Name           :
##       Telephone (primary)    :
##       Telephone (secondary)  :
##       Fax                    :
##       E-mail                 :
##     Secondary Contact
##       Contact Name           :
##       Telephone (primary)    :
##       Telephone (secondary)  :
##       Fax                    :
##       E-mail                 :
##     Additional Information   : (multiple lines)
def parseAgency(lines,begin):
	print('Parsing Agency')
	expected = '^12\.  Responsible Agency \(if different from 11\.\)(\n|\r\n?)$'
	regexp = re.compile(expected)
	resultat = regexp.search(lines[begin])
	if not resultat:
		print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (begin,expected,lines[begin]))
		sys.exit()
	begin+=1
	begin = parseComment(lines,begin,111)
        expected ='^     Preferred Abbreviation   : .*(\n|\r\n?)$'
        regexp = re.compile(expected)
	resultat = regexp.search(lines[begin])
	if not resultat:
		print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (begin,expected,lines[begin]))
		sys.exit()
	AgencyAbbrevation = lines[begin].split(": ")[1]
	AgencyAbbrevation = AgencyAbbrevation.rstrip()
	rinexheader_addline("-O.ag[ency]", AgencyAbbrevation)
	begin+=1
	begin = parseComment(lines,begin,112)
	expected = [
		'^     Primary Contact(\n|\r\n?)$',
		'^       Contact Name           : .*(\n|\r\n?)$',
		'^       Telephone \(primary\)    : .*(\n|\r\n?)$',
		'^       Telephone \(secondary\)  : .*(\n|\r\n?)$',
		'^       Fax                    : .*(\n|\r\n?)$',
		'^       E-mail                 : .*(\n|\r\n?)$',
		'^     Secondary Contact(\n|\r\n?)$',
		'^       Contact Name           : .*(\n|\r\n?)$',
		'^       Telephone \(primary\)    : .*(\n|\r\n?)$',
		'^       Telephone \(secondary\)  : .*(\n|\r\n?)$',
		'^       Fax                    : .*(\n|\r\n?)$',
		'^       E-mail                 : .*(\n|\r\n?)$',
		]
	for i in range(len(expected)):
		regexp = re.compile(expected[i])
		resultat = regexp.search(lines[i+begin])
		if not resultat:
			print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
			sys.exit()
        begin = begin +len(expected)
        begin = parseComment(lines,begin,1)
        return begin

# MORE INFO
##13.  More Information
##     Primary Data Center      :
##     Secondary Data Center    :
##     URL for More Information :
##     Hardcopy on File
##       Site Map               : (Y or URL)
##       Site Diagram           : (Y or URL)
##       Horizon Mask           : (Y or URL)
##       Monument Description  parseTemp : (Y or URL)
##       Site Pictures          : (Y or URL)
##     Additional Information   : (multiple lines)
##     Antenna Graphics with Dimensions
def parseMoreInfo(lines,begin):
	print('Parsing More Info')
	expected = [
		'^13\.  More Information(\n|\r\n?)$',
		'^     Primary Data Center      : .*(\n|\r\n?)$',
		'^     Secondary Data Center    : .*(\n|\r\n?)$',
		'^     URL for More Information : .*(\n|\r\n?)$',
		'^     Hardcopy on File(\n|\r\n?)$',
		'^       Site Map               : .*(\n|\r\n?)$',
		'^       Site Diagram           : .*(\n|\r\n?)$',
		'^       Horizon Mask           : .*(\n|\r\n?)$',
		'^       Monument Description   : .*(\n|\r\n?)$',
		'^       Site Pictures          : .*(\n|\r\n?)$',
		]
	for i in range(len(expected)):
		regexp = re.compile(expected[i])
		resultat = regexp.search(lines[i+begin])
		if not resultat:
			print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected[i],lines[i+begin]))
			sys.exit()
	begin = begin + len(expected)
	begin = parseComment(lines,begin,130)
        expected ='^     Antenna Graphics with Dimensions(\n|\r\n?)$'
        regexp = re.compile(expected)
	resultat = regexp.search(lines[begin])
	if not resultat:
		print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+begin,expected,lines[begin]))
		sys.exit() 
	return begin + 12

# creation du fichier de conf
if not cfgname:
        cfgname = siteLogName + ".cfg"
fichiercfg = open(cfgname, "w")
fichiercfg.close()
# methode pour rajouter une option au fichier de configuration
# on lit une fois le fichier on sauvergarde le tout que l'on  
# concatene avec la nouvelle option puis on reecrit le tout
def rinexheader_addline(option, lines):
	#lecture "r"
	fichiercfg = open(cfgname, "r")
	contenucfg = fichiercfg.read()
	fichiercfg.close()
	#ecriture "w"
	fichiercfg = open(cfgname, "w")
	fichiercfg.write(contenucfg)
	if option == "-O.s[ystem]" or option == "-O.pe[hEN,m]" or option == "-O.px[WGS84xyz,m]" or option == "-O.int[erval,sec]":
		argument = lines
		argument += "\n"
	else:
		argument = '"'
		argument += lines
		argument += '" \n'
	fichiercfg.write("%s %s" % (option, argument))
	fichiercfg.close()
# instanciation des premieres entrees du fichier
#rinexheader_addline("-O.r[un_by]", "OVSM")
#rinexheader_addline("-O.o[perator]", "OVSM")
#rinexheader_addline("-O.ag[ency]", "IPGP")
#rinexheader_addline("-O.int[erval,sec]", "30.000000")
#rinexheader_addline("-O.obs","C1+L1+L2+P1+P2+S1+S2")
#rinexheader_addline("-O.obs","L1+L2+ca+p2+p1")

# verification que le fichier log existe bien
#regex = re.compile('^([a-z0-9]+)\.log$')
#regex = re.compile('^([a-z0-9]{4})_([0-9]{8})\.log$')
regex = re.compile('([a-z0-9]{4})_([0-9]{8})\.log$')
resultat = regex.search(siteLogName.lower())
if resultat:
	print "Nom du fichier %s conforme." % (siteLogName)
	siteLog=open(siteLogName,'r')
	linesRaw = siteLog.readlines()
	linesNoLineFeed = [ elem for elem in linesRaw if elem != '\n' ]
	linesNoCarriage = [ elem for elem in linesNoLineFeed if elem != '\r\n' ]
	linesCleaned = [ elem for elem in linesNoCarriage if elem != '\r' ]

	nextLine = parseHeader(linesCleaned,0)

	nextLine = parseForm(linesCleaned,nextLine)
	
	nextLine = parseSiteID(linesCleaned,nextLine)
	
	nextLine = parseSiteLoc(linesCleaned,nextLine)

	startReceiver(linesCleaned[nextLine])
	nextLine = nextLine + 1
	
	found3X = False
	while linesCleaned[nextLine].startswith("3."):
		if linesCleaned[nextLine].startswith("3.x"):
			found3X = True
			expected = [
				'^3\.x  Receiver Type            : \(A20, from rcvr_ant.tab; see instructions\)',
#				'^     Satellite System         : \(GPS\/GLONASS\/GPS\+GLONASS\)',
				'^     Satellite System         : \(GPS\+GLO\+GAL\+BDS\+QZSS\+SBAS\)',
				'^     Serial Number            : \((A20, but note the first A5 is used in SINEX\))|(\(A5\))',
				'^     Firmware Version         : \(A11\)',
				'^     Elevation Cutoff Setting : \(deg\)',
				'^     Date Installed           : \(CCYY-MM-DDThh:mmZ\)',
				'^     Date Removed             : \(CCYY-MM-DDThh:mmZ\)',
				'^     Temperature Stabiliz.    : \(none or tolerance in degrees C\)',
				'^     Additional Information   : \(multiple lines\)'      
				]
			for i in range(9):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			nextLine = nextLine + 9
		else:
			if not found3X:
				nextLine = parseReceiver(linesCleaned,nextLine)
			else:
				print('Section 3 mal placee')
				sys.exit()

	startAntenna(linesCleaned[nextLine])
	nextLine = nextLine + 1

	found4X = False
	while linesCleaned[nextLine].startswith("4."):
		if linesCleaned[nextLine].startswith("4.x"):
			found4X = True
			expected = [
				'^4\.x  Antenna Type             : \(A20, from rcvr_ant.tab; see instructions\)',
				'^     Serial Number            : \(A\*, but note the first A5 is used in SINEX\)',
				'^     Antenna Reference Point  : \(BPA\/BCR\/XXX from "antenna.gra"; see instr.\)',
				'^     Marker->ARP Up Ecc. \(m\)  : \(F8.4\)',
				'^     Marker->ARP North Ecc\(m\) : \(F8.4\)',
				'^     Marker->ARP East Ecc\(m\)  : \(F8.4\)',
				'^     Alignment from True N    : \(deg; \+ is clockwise\/east\)',
				'^     Antenna Radome Type      : \(A4 from rcvr_ant.tab; see instructions\)',
				'^     Radome Serial Number     : ?',
				'^     Antenna Cable Type       : \(vendor & type number\)',
				'^     Antenna Cable Length     : \(m\)',
				'^     Date Installed           : \(CCYY-MM-DDThh:mmZ\)',
				'^     Date Removed             : \(CCYY-MM-DDThh:mmZ\)',
				'^     Additional Information   : \(multiple lines\)'
				]
			for i in range(14):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			nextLine = nextLine + 15
		else:
			if not found4X:
				nextLine = parseAntenna(linesCleaned,nextLine)
			else:
				print('Section 4 mal placee')
				sys.exit()
	
	found5X = False
	while linesCleaned[nextLine].startswith("5."):
		if linesCleaned[nextLine].startswith("5.x"):
			found5X = True
			expected = [
				'^5\.x  Tied Marker Name         : ?',
				'^     Tied Marker Usage        : \(SLR\/VLBI\/LOCAL CONTROL\/FOOTPRINT\/etc\)',
				'^     Tied Marker CDP Number   : \(A4\)',
				'^     Tied Marker DOMES Number : \(A9\)',
				'^     Differential Components from GNSS Marker to the tied monument \(ITRS\)',
				'^       dx \(m\)                 : \(m\)',
				'^       dy \(m\)                 : \(m\)',
				'^       dz \(m\)                 : \(m\)',
				'^     Accuracy \(mm\)            : \(mm\)',
				'^     Survey method            : \(GPS CAMPAIGN\/TRILATERATION\/TRIANGULATION\/etc\)',
				'^     Date Measured            : \(CCYY-MM-DDThh:mmZ\)',
				'^     Additional Information   : \(multiple lines\)'
				]
			for i in range(12):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 5x ok'
			nextLine = nextLine + 13
		else:
			if not found5X:
				nextLine = parseSite(linesCleaned,nextLine)
			else:
				print('Section 5 mal placee')
				sys.exit()
				
	found6X = False
	while linesCleaned[nextLine].startswith("6."):
		if linesCleaned[nextLine].startswith("6.x"):
			found6X = True
			expected = [
				'^6\.x  Standard Type            : \(INTERNAL or EXTERNAL H-MASER\/CESIUM\/etc\)',
				'^       Input Frequency        : \(if external\)',
				'^       Effective Dates        : \(CCYY-MM-DD\/CCYY-MM-DD\)',
				'^       Notes                  : \(multiple lines\)'
				]
			for i in range(4):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 6x ok'
			nextLine = nextLine + 5
		else:
			if not found6X:
				nextLine = parseFrequence(linesCleaned,nextLine)
			else:
				print('Section 6 mal placee')
				sys.exit()

	found7X = False
	while linesCleaned[nextLine].startswith("7."):
		if linesCleaned[nextLine].startswith("7.x"):
			found7X = True
			expected = [
				'^7\.x  Instrumentation Type     : \(GPS\/GLONASS\/DORIS\/PRARE\/SLR\/VLBI\/TIME\/etc\)$',
				'^       Status                 : \(PERMANENT\/MOBILE\)$',
				'^       Effective Dates        : \(CCYY-MM-DD\/CCYY-MM-DD\)$',
				'^       Notes                  : \(multiple lines\)'
				]
			for i in range(4):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 7x ok'
			nextLine = nextLine + 5
		else:
			if not found7X:
				nextLine = parseCollocation(linesCleaned,nextLine)
			else:
				print('Section 7 mal placee')
				sys.exit()
			

	found81X = False
	while linesCleaned[nextLine].startswith("8.1."):
		if linesCleaned[nextLine].startswith("8.1.x"):
			found81X = True
			expected = [
				'^8\.1\.x  Humidity Sensor Model  : ?',   
				'^       Manufacturer           : ?', 
				'^       Serial Number          : ?',
				'^       Data Sampling Interval : \(sec\)',
				'^       Accuracy \(% rel h\)     : \(% rel h\)',
				'^       Aspiration             : \(UNASPIRATED\/NATURAL\/FAN\/etc\)',
				'^       Height Diff to Ant     : \(m\)',
				'^       Calibration date       : \(CCYY-MM-DD\)',
				'^       Effective Dates        : \(CCYY-MM-DD\/CCYY-MM-DD\)',
				'^       Notes                  : \(multiple lines\)'
				]
			for i in range(10):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 81x ok'
			nextLine = nextLine + 10
		else:
			if not found81X:
				nextLine = parseHumidity(linesCleaned,nextLine)
			else:
				print('Section 8.1 mal placee')
				sys.exit()
	       
	found82X = False
	while linesCleaned[nextLine].startswith("8.2."):
		if linesCleaned[nextLine].startswith("8.2.x"):
			found82X = True
			expected = [
				'^8\.2\.x  Pressure Sensor Model  : ?',  
				'^       Manufacturer           : ?', 
				'^       Serial Number          : ?',
				'^       Data Sampling Interval : \(sec\)',
				'^       Accuracy               : \(hPa\)',
				'^       Height Diff to Ant     : \(m\)',
				'^       Calibration date       : \(CCYY-MM-DD\)',
				'^       Effective Dates        : \(CCYY-MM-DD\/CCYY-MM-DD\)',
				'^       Notes                  : \(multiple lines\)'
				]
			for i in range(9):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 82x ok'
			nextLine = nextLine + 9
		else:
			if not found82X:
				nextLine = parsePressure(linesCleaned,nextLine)
			else:
				print('Section 8.2 mal placee')
				sys.exit()

	found83X = False
	while linesCleaned[nextLine].startswith("8.3."):
		if linesCleaned[nextLine].startswith("8.3.x"):
			found83X = True
			expected = [
				'^8\.3\.x  Temp. Sensor Model     : ?',  
				'^       Manufacturer           : ?', 
				'^       Serial Number          : ?',
				'^       Data Sampling Interval : \(sec\)',
				'^       Accuracy               : \(deg C\)',
				'^       Aspiration             : \(UNASPIRATED\/NATURAL\/FAN\/etc\)',
				'^       Height Diff to Ant     : \(m\)',
				'^       Calibration date       : \(CCYY-MM-DD\)',
				'^       Effective Dates        : \(CCYY-MM-DD\/CCYY-MM-DD\)',
				'^       Notes                  : \(multiple lines\)'
				]
			for i in range(10):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 83x ok'
			nextLine = nextLine + 10
		else:
			if not found83X:
				nextLine = parseTemp(linesCleaned,nextLine)
			else:
				print('Section 8.3 mal placee')
				sys.exit()

	found84X = False
	while linesCleaned[nextLine].startswith("8.4."):
		if linesCleaned[nextLine].startswith("8.4.x"):
			found84X = True
			expected = [
				'^8\.4\.x  Water Vapor Radiometer : ?',  
				'^       Manufacturer           : ?', 
				'^       Serial Number          : ?',
				'^       Distance to Antenna    : \(m\)',
				'^       Height Diff to Ant     : \(m\)',
				'^       Calibration date       : \(CCYY-MM-DD\)',
				'^       Effective Dates        : \(CCYY-MM-DD\/CCYY-MM-DD\)',
				'^       Notes                  : \(multiple lines\)'
				]
			for i in range(8):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 84x ok'
			nextLine +=8
		else:
			if not found84X:
				nextLine = parseWatorVapor(linesCleaned,nextLine)
			else:
				print('Section 8.4 mal placee')
				sys.exit()
				
	found85X = False
	while linesCleaned[nextLine].startswith("8.5."):
		if linesCleaned[nextLine].startswith("8.5.x"):
			found84X = True
			expected = [
				'^8\.5\.x  Other Instrumentation  : \(multiple lines\)'
				]
			for i in range(1):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 85x ok'
			nextLine = nextLine + 2
		else:
			if not found85X:
				nextLine = parseOtherInstru(linesCleaned,nextLine)
			else:
				print('Section 8.5 mal placee')
				sys.exit()


	found91X = False
	while linesCleaned[nextLine].startswith("9.1."):
		if linesCleaned[nextLine].startswith("9.1.x"):
			found91X = True
			expected = [
				'^9\.1\.x  Radio Interferences    : \(TV\/CELL PHONE ANTENNA\/RADAR\/etc\)',   
				'^       Observed Degradations  : \(SN RATIO\/DATA GAPS\/etc\)', 
				'^       Effective Dates        : \(CCYY-MM-DD\/CCYY-MM-DD\)',
				'^       Additional Information : \(multiple lines\)'
				]
			for i in range(4):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 91x ok'
			nextLine = nextLine + 4
		else:
			if not found91X:
				nextLine = parseRadioInterferences(linesCleaned,nextLine)
			else:
				print('Section 9.1 mal placee')
				sys.exit()

	found92X = False
	while linesCleaned[nextLine].startswith("9.2."):
		if linesCleaned[nextLine].startswith("9.2.x"):
			found92X = True
			expected = [
				'^9\.2\.x  Multipath Sources      : \(METAL ROOF\/DOME\/VLBI ANTENNA\/etc\)',   
				'^       Effective Dates        : \(CCYY-MM-DD\/CCYY-MM-DD\)', 
				'^       Additional Information : \(multiple lines\)'
				   ]
			for i in range(3):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 92x ok'
			nextLine = nextLine + 3
		else:
			if not found92X:
				nextLine = parseMultipathSources(linesCleaned,nextLine)
			else:
				print('Section 9.2 mal placee')
				sys.exit()
				
	found93X = False
	while linesCleaned[nextLine].startswith("9.3."):
		if linesCleaned[nextLine].startswith("9.3.x"):
			found93X = True
			expected = [
				'^9\.3\.x  Signal Obstructions    : \(TREES\/BUILDINGS\/etc\)',   
				'^       Effective Dates        : \(CCYY-MM-DD\/CCYY-MM-DD\)', 
				'^       Additional Information : \(multiple lines\)'
				   ]
			for i in range(3):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 93x ok'
			nextLine = nextLine + 4
		else:
			if not found93X:
				nextLine = parseSignalObstructions(linesCleaned,nextLine)
			else:
				print('Section 9.3 mal placee')
				sys.exit()
	
	found10X = False
	while linesCleaned[nextLine].startswith("10."):
		if linesCleaned[nextLine].startswith("10.x"):
			found10X = True
			expected = [
				'^10\.x  Date                    : \(CCYY-MM-DD\/CCYY-MM-DD\)',   
				'^      Event                   : \(TREE CLEARING\/CONSTRUCTION\/etc\)', 
				   ]
			for i in range(2):
				regexp = re.compile(expected[i])
				resultat = regexp.search(linesCleaned[i+nextLine])
				if not resultat:
					print('Erreur sur la ligne %s.\n "%s" Attendu.\n "%s" Trouve' % (i+nextLine,expected[i],linesCleaned[i+nextLine]))
					sys.exit()
			print 'Section 10x ok'
			nextLine = nextLine + 2
		else:
			if not found10X:
				nextLine = parseLocalEpisodicEffects(linesCleaned,nextLine)
			else:
				print('Section 10 mal placee')
				sys.exit()
				

	nextLine = parseLocalAgency(linesCleaned,nextLine)

	nextLine = parseAgency(linesCleaned,nextLine)

	nextLine = parseMoreInfo(linesCleaned,nextLine)
	

