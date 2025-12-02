#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import sys



if len(sys.argv) < 2 :
  print ( "\nGive me data file name on the command line\n" )
  sys.exit ( 1 )

# --------------------- Load data ---------------------
data = np.loadtxt("router_a.data", ndmin=2)   # works for 1 or 2 columns (forces 2D array)
#data = np.loadtxt("/home/mick/skrp/results/3.4.1_x/soak/2025-11-27-22-48/graphs/soak/cpu_200_sender-threads_3_router-threads_3.data", ndmin=2)   # works for 1 or 2 columns (forces 2D array)
n_cols = data.shape[1]
x = np.arange(1, data.shape[0] + 1)
y1 = data[:, 0]
y2 = data[:, 1] if n_cols >= 2 else None

# --------------------- Create figure ---------------------
fig, ax1 = plt.subplots(figsize=(12, 7))


# ----- Make window size adaptive to user's actual screen resolution -----
from PyQt5.QtWidgets import QApplication

# Safely get (or create) the Qt application instance
app = QApplication.instance()
if app is None:
    app = QApplication([])

# Get the primary screen's available geometry (excludes taskbar/dock)
screen = app.primaryScreen()
rect = screen.availableGeometry()          # this is the usable screen area
screen_width = rect.width()
screen_height = rect.height()

# Choose your desired fraction of the screen (these values feel perfect on every monitor I've tried)
desired_width  = int(screen_width  * 0.94)   # 94 % of screen width
desired_height = int(screen_height * 0.50)   # 50 % of screen height (leaves room for title bar + taskbar)

# Apply the size and center the window
manager = fig.canvas.manager
manager.window.resize(desired_width, desired_height)
manager.window.move(int((screen_width - desired_width) / 2),
                    int((screen_height - desired_height) / 2))



# Always plot the left (red) series
ax1.plot(x, y1, color='red', lw=1.5, label="Column 1 (red - left axis)")

ax1.set_xlabel("Index", fontsize=24, color="#808080")
ax1.set_ylabel("Column 1 (left axis)", fontsize=28, color="red")
ax1.tick_params(axis='x', labelcolor="#808080", labelsize=16)
ax1.tick_params(axis='y', labelcolor="red", labelsize=20)

# Colored spines for left + bottom
ax1.spines['left'].set_color("red")
ax1.spines['left'].set_linewidth(2)
ax1.spines['bottom'].set_color("#808080")
ax1.spines['bottom'].set_linewidth(1.5)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Right (blue) axis only if we actually have a second column
ax2 = None
if y2 is not None:
    ax2 = ax1.twinx()
    ax2.plot(x, y2, color='blue', lw=1.5, label="Column 2 (blue - right axis)")
    ax2.set_ylabel("Column 2 (right axis)", fontsize=28, color="blue")
    ax2.tick_params(axis='y', labelcolor="blue", labelsize=20)
    ax2.spines['right'].set_color("blue")
    ax2.spines['right'].set_linewidth(2)
    ax2.spines['right'].set_visible(True)

# Legend (auto-combines if dual)
handles, labels = ax1.get_legend_handles_labels()
if ax2 is not None:
    h2, l2 = ax2.get_legend_handles_labels()
    handles += h2
    labels += l2
ax1.legend(handles, labels, loc='upper left', fontsize=16)

plt.title("Interactive plot (1 or 2 columns)", fontsize=20, pad=20)
plt.tight_layout()

# Store the exact original view so 'h' can restore it perfectly
initial_xlim = ax1.get_xlim()
initial_ylim1 = ax1.get_ylim()
initial_ylim2 = ax2.get_ylim() if ax2 is not None else None

# --------------------- Hover tooltip + crosshair ---------------------
vline = ax1.axvline(color='gray', lw=1.2, ls='--', alpha=0.8, visible=False)

tooltip = ax1.text(0.98, 0.98, "", transform=ax1.transAxes, ha='right', va='top',
                   fontsize=16, bbox=dict(boxstyle="round,pad=0.6", fc="white", ec="black", alpha=0.95))

axes_list = [ax1]
if ax2 is not None:
    axes_list.append(ax2)



def on_hover(event):
    if event.inaxes not in axes_list:
        vline.set_visible(False)
        tooltip.set_visible(False)
        fig.canvas.draw_idle()
        return

    idx = np.argmin(np.abs(x - event.xdata))

    vline.set_xdata([event.xdata])
    vline.set_visible(True)

    text = f"Index: {x[idx]:.0f}\n"
    text += f"Column 1 (red): {y1[idx]:.10g}"
    if y2 is not None:
        text += f"\nColumn 2 (blue): {y2[idx]:.10g}"

    tooltip.set_text(text)
    tooltip.set_visible(True)
    fig.canvas.draw_idle()

fig.canvas.mpl_connect("motion_notify_event", on_hover)




# --------------------- Keyboard zoom/pan + HOME (Gnuplot style) ---------------------
def on_key(event):
    # --- 'h' / Home / 'r' = restore original view ---
    if event.key in ('h', 'H', 'home', 'r', 'R'):
        ax1.set_xlim(initial_xlim)
        ax1.set_ylim(initial_ylim1)
        if ax2 is not None:
            ax2.set_ylim(initial_ylim2)
        fig.canvas.draw_idle()
        return

    # --- Regular zoom / pan ---
    if event.key not in ('+', '=', '-', 'left', 'right'):
        return

    cur_xlim = ax1.get_xlim()
    cur_xwidth = cur_xlim[1] - cur_xlim[0]
    x_center = (cur_xlim[0] + cur_xlim[1]) / 2

    if event.key in ('+', '='):
        scale_factor = 1 / 1.5
    elif event.key == '-':
        scale_factor = 1.5
    else:
        scale_factor = None

    if scale_factor is not None:
        # Zoom X
        new_xwidth = cur_xwidth * scale_factor
        ax1.set_xlim(x_center - new_xwidth / 2, x_center + new_xwidth / 2)

        # Zoom Y1
        cur_ylim1 = ax1.get_ylim()
        y1_center = (cur_ylim1[0] + cur_ylim1[1]) / 2
        new_y1_width = (cur_ylim1[1] - cur_ylim1[0]) * scale_factor
        ax1.set_ylim(y1_center - new_y1_width / 2, y1_center + new_y1_width / 2)

        # Zoom Y2 only if it exists
        if ax2 is not None:
            cur_ylim2 = ax2.get_ylim()
            y2_center = (cur_ylim2[0] + cur_ylim2[1]) / 2
            new_y2_width = (cur_ylim2[1] - cur_ylim2[0]) * scale_factor
            ax2.set_ylim(y2_center - new_y2_width / 2, y2_center + new_y2_width / 2)

        fig.canvas.draw_idle()
        return

    # Horizontal panning
    pan_amount = cur_xwidth * 0.2
    if event.key == 'left':
        ax1.set_xlim(cur_xlim[0] - pan_amount, cur_xlim[1] - pan_amount)
    elif event.key == 'right':
        ax1.set_xlim(cur_xlim[0] + pan_amount, cur_xlim[1] + pan_amount)

    fig.canvas.draw_idle()




fig.canvas.mpl_connect('key_press_event', on_key)

#fig.canvas.manager.window.resize(3000, 1000)

plt.show()


