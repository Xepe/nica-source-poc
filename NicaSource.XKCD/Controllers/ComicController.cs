using NicaSource.XKCD.Models;
using NicaSource.XKCD.Services;
using System;
using System.Configuration;
using System.Threading.Tasks;
using System.Web.Mvc;

namespace NicaSource.XKCD.Controllers
{
    public class ComicController : Controller 
    {
        private string _lastComicUrl;
        private string _templateUrl;

        private ComicService _comicService;

        public ComicController()
        {
            _lastComicUrl = ConfigurationManager.AppSettings.Get("RecentComicUrl");
            _templateUrl = ConfigurationManager.AppSettings.Get("ComicNumberUrl");

            _comicService = new ComicService();
        }

        public async Task<ActionResult> Index(int id)
        {
            try
            {
                var response = new GenericResponse<ComicInformation>();

                var comicUrl = string.Format(_templateUrl, id);

                var comicInformation = await _comicService.GetComicInformationAsync(comicUrl);
                var lastComicInformation = await _comicService.GetComicInformationAsync(_lastComicUrl);

                var nextComicNumber = await _comicService.GetComicNumberAsync(lastComicInformation.Num, id, true, _templateUrl);
                var previousComicNumber = await _comicService.GetComicNumberAsync(lastComicInformation.Num, id, false, _templateUrl);

                response.Result = comicInformation;
                response.NextPage = nextComicNumber;
                response.PrevPage = previousComicNumber;

                return View(response);
            }
            catch (Exception e)
            {
                throw e;
            }
        }
    }
}