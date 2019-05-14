#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include <string>
#include <bits/stdc++.h> 
#include <sys/stat.h> 
#include <sys/types.h>

using namespace std;
 
//Change this to allow Vocal Sounds
 const bool AllowVocal = false;
 
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
	bool fin = false;
	srand(time(NULL)+time(NULL));
	do{
		string FolderName;
		for(int i = 0; i < 3; i++){
			int Num = rand();
			char ch = GiveLegalChar(Num);
			FolderName.push_back(ch);
		}
		int n = FolderName.length();
		char FolderNameArr[n];
		strcpy(FolderNameArr, FolderName.c_str());
		int Comput = mkdir(FolderNameArr,777);
		if(Comput == -1){
//			cout << "ERR" << endl;
		}else{
			cout << "Created Folder Name is = " << FolderName << endl;
			fin = true;
		}
	}while(!fin);
}