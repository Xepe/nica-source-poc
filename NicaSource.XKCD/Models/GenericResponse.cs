namespace NicaSource.XKCD.Models
{
    public class GenericResponse<T>
    {
        public T Result { get; set; }
        public int NextPage { get; set; }
        public int PrevPage { get; set; }
    }
}