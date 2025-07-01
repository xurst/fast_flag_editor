import sys
import os
import ctypes
import pygame
import imgui
from imgui.integrations.pygame import PygameRenderer
from functions import FastFlagEditorApp
from PIL import Image
import OpenGL.GL as gl 

def main():

    myappid = 'roblox.fast.flag.editor.1.0.0'
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except (AttributeError, TypeError):
        print("Could not set AppUserModelID (not on Windows?).")

    pygame.init()
    pygame.display.set_caption("Roblox Fast Flag Editor")

    size = 800, 600
    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)

    try:
        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "assets", "fast_flag_editor_icon.ico"
        )
        if os.path.exists(icon_path):
            img = Image.open(icon_path)
            icon_surface = pygame.image.fromstring(img.tobytes(), img.size, img.mode)
            pygame.display.set_icon(icon_surface)
    except Exception as e:
        print(f"Warning: Could not load window icon: {e}")

    imgui.create_context()
    impl = PygameRenderer()
    io = imgui.get_io()
    io.display_size = size

    root_dir = os.path.dirname(os.path.abspath(__file__))

    # font_path = os.path.join(root_dir, "assets", "segoe-ui-semilight.ttf")

    # if os.path.exists(font_path):
    #     io.fonts.clear()
    #     segoe_font = io.fonts.add_font_from_file_ttf(font_path, 20)

    #     impl.refresh_font_texture()

    app = FastFlagEditorApp()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                size = event.size
                pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)
                io.display_size = size
            impl.process_event(event)

        if not running:
            break

        app.update()

        impl.process_inputs()
        imgui.new_frame()

        app.draw_ui()

        gl.glClearColor(0.2, 0.2, 0.2, 1.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        imgui.render()
        impl.render(imgui.get_draw_data())
        pygame.display.flip()

    impl.shutdown()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()