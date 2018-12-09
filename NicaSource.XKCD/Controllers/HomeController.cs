using NicaSource.XKCD.Models;
using NicaSource.XKCD.Services;
using System.Configuration;
using System.Threading.Tasks;
using System.Web.Mvc;

namespace NicaSource.XKCD.Controllers
{
    public class HomeController : Controller
    {
        private string _lastComicUrl;
        private string _templateUrl;

        private ComicService _comicService;

        public HomeController()
        {
            _lastComicUrl = ConfigurationManager.AppSettings.Get("RecentComicUrl");
            _templateUrl = ConfigurationManager.AppSettings.Get("ComicNumberUrl");

            _comicService = new ComicService();
        }
        public async Task<ActionResult> Index()
        {

            var response = new GenericResponse<ComicInformation>();

            var lastComicInformation = await _comicService.GetComicInformationAsync(_lastComicUrl);
            var nextComicNumber = await _comicService.GetComicNumberAsync(lastComicInformation.Num, lastComicInformation.Num, true, _templateUrl);
            var previousComicNumber = await _comicService.GetComicNumberAsync(lastComicInformation.Num, lastComicInformation.Num, false, _templateUrl);

            response.Result = lastComicInformation;
            response.NextPage = nextComicNumber;
            response.PrevPage = previousComicNumber;

            return View(response);
        }
    }
}