from django.db import models

class Movie(models.Model):
    tmdb_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    overview = models.TextField()
    poster_path = models.CharField(max_length=255, null=True, blank=True)
    backdrop_path = models.CharField(max_length=255, null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    # Y cualquier otro campo que quieras de TMDB...

    def __str__(self):
        return self.title

class VideoSource(models.Model):
    movie = models.ForeignKey(Movie, related_name='sources', on_delete=models.CASCADE)
    language = models.CharField(max_length=50) # "Latino", "Español", "Subtitulado"
    server_name = models.CharField(max_length=100) # "Streamwish", "Filemoon"
    embed_url = models.URLField(max_length=1024)

    def __str__(self):
        return f"{self.movie.title} - {self.server_name} ({self.language})"