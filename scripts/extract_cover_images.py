import argparse
import io

import boto3
import pypdf
import PIL

EXTENSION_LOOKUP = {
    format_: extension for extension, format_ in PIL.Image.registered_extensions().items()
    if extension != ".apng"
}
SOURCE_BUCKET = "pdf-pipeline-store-qa"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="")
    args = parser.parse_args()
    client = boto3.Session(profile_name=args.profile).client("s3")
    print("Listing objects from S3")
    for obj in list_pdfs(client, SOURCE_BUCKET):
        key = obj["Key"]
        if not key.endswith(".pdf"):
            print(f"Skipping {key}")
            continue
        print(f"Reading PDF for {key}")
        pdf = read_pdf(client, SOURCE_BUCKET, key)
        print(f"Finding cover for {key}")
        try:
            cover = find_cover(pdf)
        except ValueError:
            print(f"Could not find cover")
        else:
            print("Cover found, saving")
            extension = EXTENSION_LOOKUP.get(cover.format, "tiff")
            outfile = key.split("/")[-1].replace(".pdf", f"-cover{extension}")
            with open(f"covers/{outfile}", "wb") as f:
                cover.save(f)

            print(f"Saved cover to {outfile}")


def list_pdfs(client, bucket: str) -> list[dict]:
    return client.list_objects_v2(
        Bucket=bucket,
        Prefix="tagged_pdfs/",
    )["Contents"]


def read_pdf(client, bucket: str, key: str) -> pypdf.PdfReader:
    stream = io.BytesIO()
    client.download_fileobj(Bucket=bucket, Key=key, Fileobj=stream)
    return pypdf.PdfReader(stream)


def find_cover(pdf: pypdf.PdfReader) -> PIL.Image:
    for page in pdf.pages:
        image = page.images[0].image
        if page.extract_text():
            return image

        if image.entropy() < 0.001:
            continue

        return image

    raise ValueError("No cover found")


if __name__ == "__main__":
    main()
