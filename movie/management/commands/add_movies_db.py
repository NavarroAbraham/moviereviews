from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from movie.models import Movie
from pathlib import Path
import json

class Command(BaseCommand):
    help = 'Add movies to the database from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file', '-f',
            dest='file',
            default=str(Path(getattr(settings, 'BASE_DIR', Path.cwd())) / 'movies.json'),
            help='Path to movies JSON file. Defaults to <BASE_DIR>/movies.json',
        )

    def handle(self, *args, **options):
        file_arg = options.get('file')
        json_path = Path(file_arg)

        # If a relative path was provided, resolve it from BASE_DIR
        if not json_path.is_absolute():
            base_dir = Path(getattr(settings, 'BASE_DIR', Path.cwd()))
            json_path = (base_dir / json_path).resolve()

        if not json_path.exists():
            raise CommandError(f"JSON file not found: {json_path}")

        added = 0
        updated = 0
        skipped = 0

        def normalize_image(value: str | None) -> str | None:
            if not value:
                return None
            p = Path(str(value))
            media_root = Path(getattr(settings, 'MEDIA_ROOT', ''))
            try:
                if media_root and p.is_absolute():
                    rel = p.relative_to(media_root)
                    return str(rel).replace('\\', '/')
            except Exception:
                pass
            return str(value).replace('\\', '/')

        with json_path.open('r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        # Accept either a list of dicts or a dict with a common key
        if isinstance(data, dict):
            for key in ('movies', 'data', 'results', 'items'):
                if key in data and isinstance(data[key], list):
                    data = data[key]
                    break

        if not isinstance(data, list):
            raise CommandError('Expected JSON array of movie objects or a dict containing a list under "movies"/"data"/"results"/"items".')

        for idx, movie_data in enumerate(data, start=1):
            if not isinstance(movie_data, dict):
                skipped += 1
                continue

            title = (movie_data.get('title') or '').strip()
            # Map possible description fields from dataset
            description_val = (
                movie_data.get('description')
                or movie_data.get('plot')
                or movie_data.get('fullplot')
                or ''
            )
            description = str(description_val).strip()

            # Coerce year to int when possible
            year_val = movie_data.get('year')
            try:
                year = int(year_val) if year_val not in (None, '') else None
            except (ValueError, TypeError):
                year = None

            # Map image from 'image' (local) or 'poster' (external). Don't store external URLs in ImageField.
            image_src = movie_data.get('image') or ''
            image = normalize_image(image_src) if image_src else ''

            url = movie_data.get('url') or ''
            genre = (movie_data.get('genre') or '').strip()

            if not title or not description:
                skipped += 1
                continue

            lookup = {'title': title}
            if year is not None:
                lookup['year'] = year

            defaults = {
                'description': description,
                'url': url,
                'genre': genre,
            }
            # Only set image if we have a local/relative path
            if image:
                defaults['image'] = image

            obj, created = Movie.objects.update_or_create(defaults=defaults, **lookup)
            if created:
                added += 1
            else:
                updated += 1

            # Periodic progress (every 1000 items)
            if idx % 1000 == 0:
                self.stdout.write(f"Processed {idx} records... (added={added}, updated={updated}, skipped={skipped})")

        self.stdout.write(self.style.SUCCESS(
            f'Successfully processed {added + updated + skipped} records: added={added}, updated={updated}, skipped={skipped}'
        ))