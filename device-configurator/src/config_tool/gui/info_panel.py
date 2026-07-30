"""Right-hand information column: device image, company info, versions.

Shows (top to bottom):
- Company wordmark (or ``assets/logo.png`` if present)
- Device photo (``assets/device.png``; placeholder box when missing)
- Product name, company info, website link, app + device version
"""

from __future__ import annotations

import webbrowser
from typing import Optional

import customtkinter as ctk

from config_tool import __version__
from config_tool.gui import theme
from config_tool.paths import get_assets_dir

DEVICE_IMAGE_NAMES = ("device.png", "device.jpg", "device.jpeg")
LOGO_IMAGE_NAMES = ("logo.png", "logo.jpg")

IMAGE_MAX_W = 220
IMAGE_MAX_H = 200
LOGO_MAX_W = 200
LOGO_MAX_H = 64


def _load_ctk_image(names: tuple[str, ...], max_w: int, max_h: int) -> Optional[ctk.CTkImage]:
    """Load the first existing image from assets/, scaled to fit. None on failure.

    Downscaling is done here with LANCZOS resampling plus a subtle sharpen,
    which gives noticeably better quality than letting CTkImage resize.
    """
    try:
        from PIL import Image, ImageEnhance
    except ImportError:
        return None

    assets = get_assets_dir()
    for name in names:
        path = assets / name
        if path.is_file():
            try:
                img = Image.open(path).convert("RGBA")
                scale = min(max_w / img.width, max_h / img.height, 1.0)
                size = (round(img.width * scale), round(img.height * scale))
                if scale < 1.0:
                    img = img.resize(size, Image.LANCZOS)
                    img = ImageEnhance.Sharpness(img).enhance(1.2)
                return ctk.CTkImage(light_image=img, dark_image=img, size=size)
            except Exception:
                return None
    return None


class InfoPanel(ctk.CTkFrame):
    """Fixed-width company/device information column."""

    PANEL_WIDTH = 260

    def __init__(self, master, **kwargs) -> None:
        kwargs.setdefault("fg_color", theme.PANEL_BG)
        kwargs.setdefault("corner_radius", theme.CORNER_RADIUS)
        kwargs.setdefault("width", self.PANEL_WIDTH)
        super().__init__(master, **kwargs)
        self.grid_propagate(False)
        self.grid_columnconfigure(0, weight=1)
        # Row 2 (spacer) absorbs extra vertical space, pushing info to the bottom
        self.grid_rowconfigure(2, weight=1)

        # ---- Company wordmark / logo ----
        logo_img = _load_ctk_image(LOGO_IMAGE_NAMES, LOGO_MAX_W, LOGO_MAX_H)
        if logo_img is not None:
            ctk.CTkLabel(self, image=logo_img, text="").grid(
                row=0, column=0, pady=(20, 4)
            )
        else:
            ctk.CTkLabel(
                self,
                text=theme.COMPANY_SHORT,
                font=ctk.CTkFont(size=22, weight="bold"),
                text_color=(theme.PRIMARY, "#C6D3DF"),
            ).grid(row=0, column=0, pady=(20, 0))
            ctk.CTkLabel(
                self,
                text="Geotechnical Engineering",
                font=ctk.CTkFont(size=12),
                text_color=theme.TEXT_MUTED,
            ).grid(row=1, column=0, pady=(0, 4))

        # ---- Device image ----
        image_card = ctk.CTkFrame(self, fg_color=theme.CARD_BG, corner_radius=theme.CORNER_RADIUS)
        image_card.grid(row=2, column=0, sticky="n", padx=16, pady=16)

        device_img = _load_ctk_image(DEVICE_IMAGE_NAMES, IMAGE_MAX_W, IMAGE_MAX_H)
        if device_img is not None:
            ctk.CTkLabel(image_card, image=device_img, text="").pack(padx=8, pady=8)
        else:
            placeholder = ctk.CTkFrame(
                image_card,
                width=IMAGE_MAX_W,
                height=150,
                fg_color="transparent",
            )
            placeholder.pack(padx=8, pady=8)
            placeholder.pack_propagate(False)
            ctk.CTkLabel(
                placeholder,
                text="Device image\n(assets/device.png)",
                font=ctk.CTkFont(size=12),
                text_color=theme.TEXT_MUTED,
                justify="center",
            ).place(relx=0.5, rely=0.5, anchor="center")

        # ---- Product / company info (bottom) ----
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.grid(row=3, column=0, sticky="sew", padx=16, pady=(0, 16))
        info.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            info,
            text=theme.PRODUCT_NAME,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=theme.TEXT_HEADING,
            wraplength=self.PANEL_WIDTH - 40,
            justify="center",
        ).grid(row=0, column=0, pady=(0, 8))

        ctk.CTkLabel(
            info,
            text=theme.COMPANY_NAME,
            font=ctk.CTkFont(size=12),
            text_color=theme.TEXT_MUTED,
            wraplength=self.PANEL_WIDTH - 40,
            justify="center",
        ).grid(row=1, column=0)

        ctk.CTkLabel(
            info,
            text=theme.COMPANY_TAGLINE,
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED,
            wraplength=self.PANEL_WIDTH - 40,
            justify="center",
        ).grid(row=2, column=0, pady=(0, 8))

        website = ctk.CTkLabel(
            info,
            text=theme.COMPANY_WEBSITE,
            font=ctk.CTkFont(size=12, underline=True),
            text_color=theme.LINK_COLOR,
            cursor="hand2",
        )
        website.grid(row=3, column=0, pady=(0, 12))
        website.bind("<Button-1>", lambda _e: webbrowser.open(theme.COMPANY_WEBSITE_URL))

        self._version_label = ctk.CTkLabel(
            info,
            text=f"App v{__version__}",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED,
        )
        self._version_label.grid(row=4, column=0)

        self._device_label = ctk.CTkLabel(
            info,
            text="Device: not connected",
            font=ctk.CTkFont(size=11),
            text_color=theme.TEXT_MUTED,
            wraplength=self.PANEL_WIDTH - 40,
            justify="center",
        )
        self._device_label.grid(row=5, column=0)

    # ------------------------------------------------------------------

    def set_device_info(self, params) -> None:
        """Update the device line from DeviceParameters (or None on disconnect)."""
        if params is None:
            self._device_label.configure(text="Device: not connected")
            return
        hw = None
        try:
            hw = params.get("HWSTATUS")
        except Exception:
            pass
        if hw:
            self._device_label.configure(text=f"Device HW: {hw}")
        else:
            self._device_label.configure(text="Device: connected")
