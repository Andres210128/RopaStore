import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage, default_storage
from django.core.management.base import BaseCommand, CommandError

from inventario.models import Producto


class Command(BaseCommand):
    help = "Copy existing local product photos to Cloudinary."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Check which photos would be uploaded without uploading them.",
        )

    def handle(self, *args, **options):
        if not os.environ.get("CLOUDINARY_URL"):
            raise CommandError("Set CLOUDINARY_URL before migrating product photos.")
        from cloudinary_storage.storage import MediaCloudinaryStorage

        if not isinstance(default_storage, MediaCloudinaryStorage):
            raise CommandError("The default storage is not configured for Cloudinary.")

        local_storage = FileSystemStorage(location=settings.MEDIA_ROOT)
        products = list(Producto.objects.exclude(fotografia=""))
        pending_uploads = []
        missing_files = []

        for producto in products:
            name = producto.fotografia.name
            if default_storage.exists(name):
                continue
            if not local_storage.exists(name):
                missing_files.append(name)
                continue
            pending_uploads.append((producto, name))

        if missing_files:
            missing_names = ", ".join(missing_files)
            raise CommandError(
                f"Local photo files were not found in MEDIA_ROOT: {missing_names}"
            )

        if options["dry_run"]:
            self.stdout.write(
                self.style.WARNING(
                    f"{len(pending_uploads)} product photo(s) would be uploaded."
                )
            )
            return

        for producto, name in pending_uploads:
            with local_storage.open(name, "rb") as photo:
                producto.fotografia.save(name, photo, save=True)
            self.stdout.write(f"Uploaded product photo for product #{producto.pk}.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Uploaded {len(pending_uploads)} product photo(s)."
            )
        )
