using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Net;
using System.Threading;

namespace Scanner
{
    class Program
    {
        static void Main(string[] args)
        {
            // The code provided will print ‘Hello World’ to the console.
            // Press Ctrl+F5 (or go to Debug > Start Without Debugging) to run your app.
            Console.WriteLine("Hello World!");

            while (true)
            {
                string result = ClientDownload();
                Console.WriteLine(result);
                WebClient client = new WebClient();
                string reply = client.DownloadString("https://assess.girlsgocyberstart.org/challenge-files/get-flag?verify=ZukgeTY5HQlu1%2FL7oIkADg%3D%3D&string=" + result);
                Console.WriteLine(reply);
                DelayWait();
            };


            // Go to http://aka.ms/dotnet-get-started-console to continue learning how to build a console app! 
        }

        static string CrCeate(int number)
        {
            string str = "https://assess.girlsgocyberstart.org/challenge-files/clock-pt" + number.ToString() + "?verify=ZukgeTYSHQ1u1/170IKADg==";
            return str;
        }

        static string ClientDownload()
        {
            WebClient client = new WebClient();
            StringBuilder builder = new StringBuilder();
            for(int i = 1; i < 6; i++)
            {
                builder.Append(client.DownloadString(CrCeate(i)));
            }
            return builder.ToString();
        }

        static void DelayWait()
        {
            for(int i = 1; i < 11; i++)
            {
                Console.Write(i);
                Console.Write("...");
                Thread.Sleep(1000);
            }
            ClearCurrentConsoleLine();
        }

        static void ClearCurrentConsoleLine()
        {
            int currentLineCursor = Console.CursorTop;
            Console.SetCursorPosition(0, Console.CursorTop);
            Console.Write(new string(' ', Console.WindowWidth));
            Console.SetCursorPosition(0, currentLineCursor);
        }
    }
}
