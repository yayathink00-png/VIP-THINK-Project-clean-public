# Workflow

## High-Level Flow

```text
source requirement table
  -> normalize into row-based material task table
  -> inspect task fields
  -> generate one test image per direction
  -> human review and direction approval
  -> expand approved directions to batch output
  -> upload approved attachments
  -> verify attachment count
  -> update task status
```

## Production Controls

- Image generation is not treated as automatically public.
- Generated images require brand, copyright, likeness, and commercial-use review.
- Platform resource identifiers are not included in public documentation.

## Work Details Worth Reporting

- The project solved a real data-structure problem, not only an image-generation problem.
- The old table shape made attachment回填 unreliable; the new row-based model makes each material direction independently trackable.
- Upload success is not treated as enough; the workflow verifies attachment visibility and count.
- Output directory planning is part of the system, because preview images, ZIPs, and test images can otherwise be uploaded by mistake.

## Governance Gates

- No generated PNG/JPG assets in public Git.
- No ZIP output packages in public Git.
- No real platform resource links in public Git.
- No production attachment records in public Git.

