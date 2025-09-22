import os
from io import BytesIO
from typing import Any, Dict, Literal, Optional, Tuple, cast

import cv2
import fitz
import numpy as np
import numpy.typing as npt
from fastapi import HTTPException, UploadFile
from imagecodecs import jpegxl_encode
from PIL import Image


def encode_image_array(
    image_array: npt.NDArray[Any],
    encoder: Literal["jpg", "png", "jxl", "jxl_lossless"] = "png",
    color_space: Literal["RGB", "BGR"] = "RGB",
) -> bytes:
    """Encode image array to bytes.

    Input image range supposed to be 0-1 for `jpg`|`png` encoder.

    Args:
        image_array (numpy.ndarray): image array
        format (str): image format, can be 'png' or 'jpg'

    Returns:
        bytes: image buffer
    """
    if encoder == "jxl" or encoder == "jxl_lossless":
        if image_array.dtype not in [np.uint8, np.uint16]:
            image_array = image_array.astype(np.uint16, casting="safe")
        if encoder == "jxl":
            level = 99
        elif encoder == "jxl_lossless":
            level = 100
        return _encode_jpeg_xl(image_array, effort=3, level=level, lossless=level == 100)

    return _encode_with_opencv(image_array, encoder=encoder, color_space=color_space)


def _encode_with_opencv(
    image_array: npt.NDArray[Any],
    encoder: Literal["jpg", "png"] = "png",
    color_space: Literal["RGB", "BGR"] = "RGB",
) -> bytes:
    image_array = cast_image(image_array, dtype="uint8")

    if len(image_array.shape) == 2:
        channels = 1
    else:
        channels = image_array.shape[-1]

    if color_space == "RGB":
        if channels == 3:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        elif channels == 4:
            image_array = cv2.cvtColor(image_array, cv2.COLOR_RGBA2BGRA)

    if encoder == "jpg":
        return cv2.imencode(
            ".jpg",
            image_array,
            params=[cv2.IMWRITE_JPEG_QUALITY, 95],
        )[1].tobytes()
    elif encoder == "png":
        return cv2.imencode(".png", image_array, params=[cv2.IMWRITE_PNG_COMPRESSION, 3])[
            1
        ].tobytes()

    raise Exception("Unrecognized image format: Please choose either 'png'/ 'jpg'")


def cast_image(image_array: npt.NDArray[Any], dtype: str = "uint8") -> npt.NDArray[Any]:
    """Cast an image to a given dtype.

    Args:
        image_array (np.ndarray): image array
        dtype (str): dtype to cast to

    Returns:
        np.ndarray: image array with cast dtype
    """
    convert_dtype = np.dtype(dtype)
    if convert_dtype == np.uint8:
        if image_array.dtype == np.uint8:
            return image_array
        elif image_array.dtype in [np.float32, np.float64]:
            return cast(npt.NDArray[np.uint8], np.round(image_array * 255.0).astype(np.uint8))
        else:
            raise NotImplementedError("image_array dtype should be uint8 or float32-64")
    elif convert_dtype == np.float32:
        if image_array.dtype == np.float32:
            return image_array
        elif image_array.dtype == np.float64:
            return image_array.astype(np.float32)
        elif image_array.dtype == np.uint8:
            return image_array.astype(np.float32) / 255.0
        else:
            raise NotImplementedError("image_array dtype should be uint8 or float32-64")
    else:
        raise NotImplementedError("dtype must be either uint8 or float32")


def _encode_jpeg_xl(
    image_array: npt.NDArray[Any],
    level: int = 99,
    effort: int = 3,
    distance: Optional[float] = None,
    lossless: bool = False,
    decodingspeed: Optional[int] = None,
    photometric: Optional[int] = None,
    bitspersample: Optional[int] = None,
    planar: Optional[bool] = None,
    usecontainer: bool = True,
    numthreads: Optional[int] = None,
) -> bytes:
    """Encode image as jpeg xl.

    Args:
        image_array: image array to encode
        level: Compression level. Defaults to 99.
        effort: Encoder effort, with higher values indicating more computational
            expense for potentially better compression. Defaults to 3.
        distance: Target psychovisual difference (0 for lossless, higher for lossy).
            Defaults to None.
        lossless: Whether to encode losslessly. Defaults to False.
        decodingspeed: Target decoding speed tier.
        photometric: Color space of the input image.
            Defaults to JPEGXL.COLOR_SPACE.GRAY.
        bitspersample: Bit depth of the input image. Defaults to 16.
        planar: Whether the input image is in planar format. Defaults to None.
        usecontainer: Whether to use the JPEG XL container format. Defaults to True.
        numthreads:  Number of threads to use for encoding. Defaults to .

    """
    if numthreads is None:
        numthreads = os.cpu_count()

    return jpegxl_encode(
        image_array,
        level=level,
        effort=effort,
        distance=distance,
        lossless=lossless,
        decodingspeed=decodingspeed,
        photometric=photometric,
        bitspersample=bitspersample,
        planar=planar,
        usecontainer=usecontainer,
        numthreads=numthreads,
    )


def extract_image_array(
    uploaded_file: UploadFile,
    convert_rgb: bool = True,
) -> Tuple[npt.NDArray[Any], Dict[str, Any]]:
    """
    Lit un UploadFile et retourne (array, meta).
    - Supporte les formats images (png/jpg/jpeg/...) via Pillow.

    Retour :
      (numpy_array, metadata_dict)
      metadata_dict contient: width, height, mode, format, size_bytes
    Lève HTTPException en cas d'erreur lisible côté client.
    """
    try:
        uploaded_file.file.seek(0)
        data = uploaded_file.file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Impossible de lire le fichier: {e}")

    img: Optional[Image.Image] = None

    try:
        img = Image.open(BytesIO(data))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur lors de l'ouverture de l'image: {e}")

    try:
        if convert_rgb:
            img = img.convert("RGB")
        arr = np.asarray(img)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la conversion de l'image: {e}")

    meta: Dict[str, Any] = {
        "width": img.width,
        "height": img.height,
        "mode": img.mode,
        "format": getattr(img, "format", None),
        "size_bytes": len(data),
    }

    try:
        uploaded_file.file.seek(0)
    except Exception:
        pass

    return arr, meta


def pdf_to_image_array(
    file: UploadFile,
) -> Tuple[npt.NDArray[Any], Dict[str, Any]]:
    """Convertit la première page d'un PDF en image (numpy array) et retourne les métadonnées.

    Args:
        file (UploadFile): Le fichier PDF à convertir.
    Returns:
        Tuple[npt.NDArray[Any], Dict[str, Any]]: image_array, metadatas.
    Raises:
        HTTPException: Si le PDF ne peut pas être lu ou converti.
    """
    try:
        file.file.seek(0)
        pdf_bytes = file.file.read()

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(0)
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        pil_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        image_array = np.asarray(pil_img)

        metadatas = {
            "width": pil_img.width,
            "height": pil_img.height,
            "mode": pil_img.mode,
            "format": "PDF",
            "size_bytes": len(pdf_bytes),
        }

        doc.close()

    except Exception as e:
        print('AHH OKOK ')
        raise HTTPException(status_code=400, detail=f"Impossible de convertir le PDF en image: {e}")

    return image_array, metadatas
