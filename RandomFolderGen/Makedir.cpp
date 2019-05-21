#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string>
#include <bits/stdc++.h> 
#include <sys/stat.h> 
#include <sys/types.h>

using namespace std;
 
//Change this to allow Vocal Sounds
const bool AllowVocal = false;
//Return char from a number
//Should just make a char int function tbh
//Rather that this monstrosity 
char GiveLegalChar(int Number){
	 if(AllowVocal){
			const char VocalSounds[26] = {'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z'};
			if(Number > 26){
				Number = Number % 26;
			}
			return VocalSounds[Number];
			
	 }else{
			const char NoVocalSounds[21] = {'B','C','D','F','G','H','J','K','L','M','N','P','Q','R','S','T','V','W','X','Y','Z'};
			if(Number > 21){
				Number = Number % 21;
			}
			return NoVocalSounds[Number];
	 }	
}

int main(){
	int LoopCount = 0;
	bool fin = false;
	srand(time(NULL)+time(NULL)); //dunno why just why
	do{
		string FolderName;//Create A Null Terminated String
		
		//Fill it with random Characters
		for(int i = 0; i < 3; i++){
			int Num = rand();
			char ch = GiveLegalChar(Num);
			FolderName.push_back(ch);
		}
		
		//Removing nulls
		int n = FolderName.length(); // Get the Length of text without null
		char FolderNameArr[n]; //Create an array the size of text without null
		strcpy(FolderNameArr, FolderName.c_str()); //Copy The text Without Null Termination
		
		//Make the Folder
		int Comput = mkdir(FolderNameArr,777);
		//Checks if it error
		if(Comput == -1){
			LoopCount++;
		}else{
			cout << "Total Loop = " << LoopCount << endl;
			cout << "Created Folder Name is = " << FolderName << endl;
			fin = true;
		}
	}while(!fin); //While False
}
