use gpui_kit::component::{
    input::{InputState, TextareaState},
    Theme, ThemeMode,
};
use gpui_kit::{prelude::*, *};

#[derive(Clone, Copy, Debug, PartialEq)]
enum GlassMode {
    Window,
    Sidebar,
}

struct Probe {
    mode: GlassMode,
    opacity: f32,
    composition: Entity<TextareaState>,
    secondary: Entity<InputState>,
}

impl Probe {
    fn new(mode: GlassMode, opacity: f32, window: &mut Window, cx: &mut Context<Self>) -> Self {
        Self {
            mode,
            opacity,
            composition: cx.new(|cx| TextareaState::new(window, cx).rows(4)),
            secondary: cx.new(|cx| InputState::new(window, cx)),
        }
    }
}

impl Render for Probe {
    fn render(&mut self, _: &mut Window, _: &mut Context<Self>) -> impl IntoElement {
        div().size_full()
    }
}

fn window_options(cx: &App) -> WindowOptions {
    WindowOptions {
        window_bounds: Some(WindowBounds::Windowed(Bounds::centered(
            None,
            size(px(1000.), px(760.)),
            cx,
        ))),
        titlebar: Some(TitlebarOptions {
            title: Some("T-025 · GPUI 中文与玻璃探针".into()),
            ..Default::default()
        }),
        window_background: WindowBackgroundAppearance::Blurred,
        window_min_size: Some(size(px(850.), px(700.))),
        ..Default::default()
    }
}

fn main() {
    gpui_kit::application().run(|cx| {
        gpui_kit::init(cx);
        Theme::change(ThemeMode::Light, None, cx);
        gpui_kit::open_window(window_options(cx), cx, |window, cx| {
            cx.new(|cx| Probe::new(GlassMode::Sidebar, 0.75, window, cx))
        })
        .expect("open T-025 probe window");
        cx.activate(true);
        cx.on_window_closed(|cx| {
            if cx.windows().is_empty() {
                cx.quit();
            }
        })
        .detach();
    });
}

#[cfg(test)]
mod tests;
