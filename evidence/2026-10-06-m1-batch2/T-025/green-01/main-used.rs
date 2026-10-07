use gpui_kit::component::{
    button::Button,
    input::{Input, InputState, Textarea, TextareaState},
    text::{SelectionFormat, TextView},
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
            composition: cx.new(|cx| TextareaState::new(window, cx).rows(4).placeholder("用系统拼音输入；Return 换行")),
            secondary: cx.new(|cx| InputState::new(window, cx).placeholder("切换到这里继续输入")),
        }
    }
}

impl Render for Probe {
    fn render(&mut self, _: &mut Window, cx: &mut Context<Self>) -> impl IntoElement {
        let mode_label = match self.mode {
            GlassMode::Window => "整窗半透明",
            GlassMode::Sidebar => "仅侧栏半透明",
        };
        let status = SharedString::from(format!("{mode_label} · 不透明度 {:.0}%", self.opacity * 100.));
        let main_alpha = match self.mode {
            GlassMode::Window => self.opacity,
            GlassMode::Sidebar => 1.,
        };
        div()
            .size_full()
            .flex()
            .text_color(rgb(0x25312f))
            .child(
                div()
                    .w(px(244.))
                    .h_full()
                    .flex_shrink_0()
                    .flex()
                    .flex_col()
                    .p_5()
                    .gap_4()
                    .bg(rgb(0xe4eee9).alpha(self.opacity))
                    .border_r_1()
                    .border_color(rgb(0x25312f).alpha(0.12))
                    .child(div().text_xl().font_weight(FontWeight::SEMIBOLD).child("Muster"))
                    .child(div().text_sm().child("T-025 · 中文与玻璃探针"))
                    .child(div().mt_4().text_sm().child("玻璃范围"))
                    .child(Button::new("whole-window").label("整窗半透明").on_click(cx.listener(|this, _, _, cx| {
                        this.mode = GlassMode::Window;
                        cx.notify();
                    })))
                    .child(Button::new("sidebar-only").label("仅侧栏半透明").on_click(cx.listener(|this, _, _, cx| {
                        this.mode = GlassMode::Sidebar;
                        cx.notify();
                    })))
                    .child(div().mt_4().text_sm().child("不透明度"))
                    .child(
                        div().flex().gap_2().children(
                            [("opacity-low", 0.35, "35%"), ("opacity-mid", 0.75, "75%"), ("opacity-high", 0.95, "95%")]
                                .map(|(id, opacity, label)| Button::new(id).label(label).on_click(cx.listener(move |this, _, _, cx| {
                                    this.opacity = opacity;
                                    cx.notify();
                                }))),
                        ),
                    )
                    .child(div().text_sm().child("值越低，背景越明显。"))
                    .child(
                        div().id("glass-status").test_support().role(Role::Status)
                            .aria_label(status.clone()).text_sm().child(status),
                    )
                    .child(div().mt_4().text_sm().child("输入法、跨段复制和观感等待真人手测。")),
            )
            .child(
                div().id("main-content").flex_1().min_w_0().h_full().overflow_y_scroll()
                    .flex().flex_col().p_6().gap_4()
                    .bg(rgb(0xf8faf8).alpha(main_alpha))
                    .child(div().text_2xl().font_weight(FontWeight::SEMIBOLD).child("会话复盘：证据引用"))
                    .child(div().text_sm().child("按 MANUAL-CHECK.md 使用系统拼音，再把正文复制到文本编辑。"))
                    .child(div().text_sm().child("中文输入"))
                    .child(Textarea::new(&self.composition).aria_label("中文输入").w_full())
                    .child(div().text_sm().child("另一输入框"))
                    .child(Input::new(&self.secondary).id("secondary").aria_label("另一输入框").w_full())
                    .child(div().mt_4().text_lg().font_weight(FontWeight::SEMIBOLD).child("跨段复制样例"))
                    .child(
                        div().id("markdown-region").test_support().w_full()
                            .child(TextView::markdown("sample-markdown", include_str!("../sample.md"))
                                .selectable(true).selection_format(SelectionFormat::Plain).w_full()),
                    ),
            )
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

fn open_probe(cx: &mut App, mode: GlassMode, opacity: f32) -> (AnyWindowHandle, Entity<Probe>) {
    let result = gpui_kit::open_window(window_options(cx), cx, |window, cx| {
        cx.new(|cx| Probe::new(mode, opacity, window, cx))
    }).expect("open T-025 probe window");
    // Component's Root paints its theme background by default. Clearing that
    // single owning surface lets the window-level blur show through our panels.
    result.0.downcast::<gpui_kit::base::Root>().expect("Base Root")
        .update(cx, |root, _, cx| {
            root.style().background = Some(rgba(0x00000000).into());
            cx.notify();
        }).expect("configure transparent probe root");
    result
}

fn startup_options() -> std::result::Result<(GlassMode, f32), String> {
    let mut mode = GlassMode::Sidebar;
    let mut opacity = 0.75;
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--glass" => mode = match args.next().as_deref() {
                Some("window") => GlassMode::Window,
                Some("sidebar") => GlassMode::Sidebar,
                _ => return Err("--glass 必须为 window 或 sidebar".into()),
            },
            "--opacity" => {
                opacity = args.next().ok_or("--opacity 缺少数值")?
                    .parse::<f32>().map_err(|_| "--opacity 必须为数值")?;
                if !opacity.is_finite() || !(0.10..=0.95).contains(&opacity) {
                    return Err("--opacity 必须介于 0.10 和 0.95 之间".into());
                }
            },
            "--help" | "-h" => {
                println!("T-025 GPUI 探针：--glass sidebar|window --opacity 0.10..0.95");
                std::process::exit(0);
            },
            _ => return Err(format!("未知参数：{arg}")),
        }
    }
    Ok((mode, opacity))
}

fn main() {
    let (mode, opacity) = startup_options().unwrap_or_else(|message| {
        eprintln!("{message}");
        std::process::exit(2);
    });
    gpui_kit::application().with_assets(gpui_kit::assets::Assets).run(move |cx| {
        gpui_kit::init(cx);
        Theme::change(ThemeMode::Light, None, cx);
        open_probe(cx, mode, opacity);
        cx.activate(true);
        println!("T025_WINDOW_OPEN pid={} glass={mode:?} opacity={opacity}", std::process::id());
        cx.on_window_closed(|cx, _| {
            if cx.windows().is_empty() {
                cx.quit();
            }
        })
        .detach();
    });
}

#[cfg(test)]
mod tests;
