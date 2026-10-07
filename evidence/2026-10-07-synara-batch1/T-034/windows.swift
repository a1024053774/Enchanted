import Foundation
import CoreGraphics

let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
let own = windows.filter {
    ($0[kCGWindowOwnerName as String] as? String) == "Synara Cua"
        && ($0[kCGWindowLayer as String] as? Int) == 0
}
let data = try JSONSerialization.data(withJSONObject: own, options: [.sortedKeys])
print(String(decoding: data, as: UTF8.self))
