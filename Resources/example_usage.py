"""
Example usage of the Material 3 theme with CustomTkinter.

This demonstrates how to use the theme module in a CustomTkinter application.

Requirements:
    pip install customtkinter
"""

import customtkinter as ctk
from theme import apply_material3_theme, light_theme, dark_theme, get_color


class ExampleApp(ctk.CTk):
    """Example application demonstrating the Material 3 theme."""
    
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("Material 3 Theme Demo")
        self.geometry("800x600")
        
        # Apply the theme
        # Option 1: Use the convenience function
        apply_material3_theme("light")  # or "dark" or "system"
        
        # Option 2: Manually set theme
        # ctk.set_appearance_mode("dark")
        # ctk.set_default_color_theme(dark_theme)
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface with various widgets."""
        
        # Create a frame for the main content
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Title label
        title_label = ctk.CTkLabel(
            main_frame,
            text="Material 3 Theme Demo",
            font=("JetBrains Mono", 24, "bold")
        )
        title_label.pack(pady=10)
        
        # Description
        desc_label = ctk.CTkLabel(
            main_frame,
            text="This demonstrates the Material 3 color scheme adapted for CustomTkinter.",
            font=("JetBrains Mono", 14),
            text_color="#44474E"  # on_surface_variant
        )
        desc_label.pack(pady=5)
        
        # Theme switcher frame
        theme_frame = ctk.CTkFrame(main_frame, fg_color="#EDEDF4")  # surface_container
        theme_frame.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(
            theme_frame,
            text="Theme:",
            font=("JetBrains Mono", 14, "bold")
        ).pack(side="left", padx=10, pady=10)
        
        # Radio buttons for theme selection
        self.theme_var = ctk.StringVar(value="light")
        
        ctk.CTkRadioButton(
            theme_frame,
            text="Light",
            variable=self.theme_var,
            value="light",
            command=self._change_theme
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkRadioButton(
            theme_frame,
            text="Dark",
            variable=self.theme_var,
            value="dark",
            command=self._change_theme
        ).pack(side="left", padx=5, pady=10)
        
        ctk.CTkRadioButton(
            theme_frame,
            text="System",
            variable=self.theme_var,
            value="system",
            command=self._change_theme
        ).pack(side="left", padx=5, pady=10)
        
        # Color palette display
        colors_frame = ctk.CTkFrame(main_frame)
        colors_frame.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(
            colors_frame,
            text="Material 3 Color Palette",
            font=("JetBrains Mono", 16, "bold")
        ).pack(pady=(0, 10))
        
        # Create color swatches
        color_data = [
            ("Primary", "#415F91", get_color("primary")),
            ("Primary Container", "#D6E3FF", get_color("primary_container")),
            ("Secondary", "#565F71", get_color("secondary")),
            ("Secondary Container", "#DAE2F9", get_color("secondary_container")),
            ("Tertiary", "#705575", get_color("tertiary")),
            ("Error", "#BA1A1A", get_color("error")),
            ("Background", "#F9F9FF", get_color("background")),
            ("Surface", "#F9F9FF", get_color("surface")),
        ]
        
        for i, (name, original, current) in enumerate(color_data):
            color_row = ctk.CTkFrame(colors_frame)
            color_row.pack(fill="x", pady=5)
            
            # Color name
            label = ctk.CTkLabel(
                color_row,
                text=name,
                font=("JetBrains Mono", 12),
                width=150,
                anchor="w"
            )
            label.pack(side="left", padx=5)
            
            # Original color (from Material 3)
            orig_swatch = ctk.CTkFrame(
                color_row,
                fg_color=original,
                width=50,
                height=30
            )
            orig_swatch.pack(side="left", padx=5)
            
            # Current color (from theme)
            current_swatch = ctk.CTkFrame(
                color_row,
                fg_color=current,
                width=50,
                height=30
            )
            current_swatch.pack(side="left", padx=5)
        
        # Sample widgets
        widgets_frame = ctk.CTkFrame(main_frame)
        widgets_frame.pack(pady=20, padx=20, fill="x")
        
        ctk.CTkLabel(
            widgets_frame,
            text="Sample Widgets",
            font=("JetBrains Mono", 16, "bold")
        ).pack(pady=(0, 10))
        
        # Buttons
        ctk.CTkButton(
            widgets_frame,
            text="Primary Button",
            command=lambda: print("Primary button clicked")
        ).pack(pady=5, fill="x")
        
        ctk.CTkButton(
            widgets_frame,
            text="Secondary Button",
            fg_color=get_color("secondary"),
            hover_color=get_color("secondary_container"),
            command=lambda: print("Secondary button clicked")
        ).pack(pady=5, fill="x")
        
        # Entry
        entry = ctk.CTkEntry(widgets_frame, placeholder_text="Enter text...")
        entry.pack(pady=5, fill="x")
        
        # Switch
        switch = ctk.CTkSwitch(
            widgets_frame,
            text="Toggle Switch",
            command=lambda: print(f"Switch: {switch.get()}")
        )
        switch.pack(pady=5)
        
        # Slider
        slider = ctk.CTkSlider(
            widgets_frame,
            from_=0,
            to=100,
            command=lambda value: print(f"Slider: {value}")
        )
        slider.pack(pady=5, fill="x")
        
        # Progress bar
        progress = ctk.CTkProgressBar(widgets_frame)
        progress.pack(pady=5, fill="x")
        progress.set(0.5)
        
        # Tab view
        tabview = ctk.CTkTabview(widgets_frame)
        tabview.pack(pady=10, fill="x")
        
        tab1 = tabview.add("Tab 1")
        tab2 = tabview.add("Tab 2")
        
        ctk.CTkLabel(tab1, text="Content for Tab 1").pack(pady=10)
        ctk.CTkLabel(tab2, text="Content for Tab 2").pack(pady=10)
        
        # Checkbox
        checkbox = ctk.CTkCheckBox(
            widgets_frame,
            text="Check me",
            command=lambda: print(f"Checkbox: {checkbox.get()}")
        )
        checkbox.pack(pady=5)
        
        # Radio buttons
        radio_var = ctk.StringVar()
        ctk.CTkRadioButton(
            widgets_frame,
            text="Option 1",
            variable=radio_var,
            value="option1"
        ).pack(pady=2)
        ctk.CTkRadioButton(
            widgets_frame,
            text="Option 2",
            variable=radio_var,
            value="option2"
        ).pack(pady=2)
    
    def _change_theme(self):
        """Change the theme based on the selected option."""
        theme = self.theme_var.get()
        apply_material3_theme(theme)
        
        # Update all color swatches to reflect the new theme
        # This is a simple approach; in a real app, you might want to
        # recreate the UI or have a more sophisticated update mechanism
        print(f"Theme changed to: {theme}")


def main():
    """Run the example application."""
    # Set the appearance mode before creating the app
    # This must be done before creating any CTk widgets
    ctk.set_appearance_mode("light")
    
    app = ExampleApp()
    app.mainloop()


if __name__ == "__main__":
    main()
