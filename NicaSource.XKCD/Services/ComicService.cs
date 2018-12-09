using NicaSource.XKCD.Models;
using System.Net;
using System.Net.Http;
using System.Threading.Tasks;
using System.Web.Script.Serialization;

namespace NicaSource.XKCD.Services
{
    public class ComicService
    {
        public async Task<int> GetComicNumberAsync(int lastComicNumber, int currentComicNumber, bool isNext, string url)
        {
            var min = isNext ? currentComicNumber : 0;

            if (lastComicNumber == min)
            {
                return 0;
            }

            currentComicNumber = isNext ? currentComicNumber + 1 : currentComicNumber - 1;

            var nextComicUrl = string.Format(url, currentComicNumber);
            var response = await GetResponseAsync(nextComicUrl);

            if (response.StatusCode == HttpStatusCode.NotFound)
            {
                return await GetComicNumberAsync(lastComicNumber, currentComicNumber, isNext, url);
            }

            return currentComicNumber;
        }

        public async Task<ComicInformation> GetComicInformationAsync(string url)
        {
            var response = await GetResponseAsync(url);

            var serializer = new JavaScriptSerializer();
            var responseAsString = await response.Content.ReadAsStringAsync();

            var comicPage = serializer.Deserialize<ComicInformation>(responseAsString);

            return comicPage;
        }
        public async Task<HttpResponseMessage> GetResponseAsync(string url)
        {
            using (var client = new HttpClient())
            {
                return await client.GetAsync(url);
            }
        }
    }
}