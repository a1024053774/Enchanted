// Acceptance expectations come from the T-025 brief, not from Probe's state.
use super::{Probe, GlassMode, window_options};
use gpui_kit::{AppContext, TestAppContext, WindowBackgroundAppearance};
use gpui_kit::test::TestWindowExt;

#[gpui_kit::test]
fn controls_and_multiline_focus_render_through_the_real_view(cx: &mut TestAppContext) {
    cx.update(gpui_kit::init);
    let (handle, _) = cx.update(|cx| {
        let options = window_options(cx);
        assert_eq!(options.window_background, WindowBackgroundAppearance::Blurred);
        gpui_kit::open_window(options, cx, |window, cx| {
            cx.new(|cx| Probe::new(GlassMode::Sidebar, 0.75, window, cx))
        }).expect("open probe")
    });
    cx.update_window(handle, |_, window, cx| {
        window.render_frame(cx);
        assert_eq!(window.find("glass-status").label(), Some("仅侧栏半透明 · 不透明度 75%"));
        window.click("whole-window", cx);
        assert_eq!(window.find("glass-status").label(), Some("整窗半透明 · 不透明度 75%"));
        window.click("opacity-low", cx);
        assert_eq!(window.find("glass-status").label(), Some("整窗半透明 · 不透明度 35%"));
        window.click("sidebar-only", cx);
        assert_eq!(window.find("glass-status").label(), Some("仅侧栏半透明 · 不透明度 35%"));
        window.click("composition", cx);
        window.input("会话复盘：证据引用", cx);
        window.press("enter", cx);
        window.input("第二行 🧭", cx);
        assert_eq!(window.find("composition").value(), Some("会话复盘：证据引用\n第二行 🧭"));
        window.click("secondary", cx);
        window.input("另一输入框", cx);
        assert_eq!(window.find("secondary").value(), Some("另一输入框"));
        assert_eq!(window.find("composition").value(), Some("会话复盘：证据引用\n第二行 🧭"));
        assert!(window.find("markdown-region").bounds().size.height > gpui_kit::px(0.));
    }).unwrap();
}
