using System;
using System.Collections.Generic;
using System.Linq;
using System.Web;

namespace NicaSource.XKCD.Models
{
    public class ComicInformation
    {
        public string Month { get; set; }
        public string Img { get; set; }
        public int Num { get; set; }
        public string Title { get; set; }
        public string Alt { get; set; }
    }
}