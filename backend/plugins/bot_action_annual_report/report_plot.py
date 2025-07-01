import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import seaborn as sns
import matplotlib.font_manager as fm
from scipy.interpolate import make_interp_spline
from scipy.ndimage import gaussian_filter1d
from matplotlib.colors import LinearSegmentedColormap
from io import BytesIO

CURRENT_YEAR = 2024


def get_most_active_hour_period(hour_count, window_size=6):
    most_active = np.argmax(np.convolve(
        np.tile(hour_count, 3), np.ones(window_size), 'same')[24:48])
    left = most_active - window_size//2
    right = most_active + (window_size-1)//2
    return left, right


def get_most_active_hour(hour_count):
    return np.argmax(hour_count)


def get_most_active_day(day_count):
    return np.argmax(day_count)


def get_month_post_count(day_count):
    month_first_days = [(datetime(CURRENT_YEAR, month, 1).timetuple(
    ).tm_yday-1)/7-0.5 for month in range(1, 13)]
    month_posts = np.zeros(12)
    month_avg_posts = np.zeros(12)
    for i in range(12):
        month_posts[i] = np.sum(
            day_count[int(month_first_days[i]):int(month_first_days[i+1])])
        month_avg_posts[i] = month_posts[i] / \
            (month_first_days[i+1] - month_first_days[i])
    return month_posts, month_avg_posts


def get_most_active_month(month_avg_posts):
    return np.argmax(month_avg_posts)


def plot_post_activity_hour(post_hour):
    x = np.arange(24*3)
    y = np.tile(post_hour, 3)
    y = gaussian_filter1d(y, sigma=0.7)
    m = make_interp_spline(x, y, k=5)
    xs = np.linspace(24, 48, 1000)
    ys = m(xs)

    colors = ['blue', 'red', 'orange']
    cmap = LinearSegmentedColormap.from_list('mycmap', colors)

    most_active_period = get_most_active_hour_period(post_hour, window_size=6)
    most_active_hour = get_most_active_hour(post_hour)

    plt.figure(figsize=(9, 3))

    if most_active_period[0] < 0:
        plt.axvspan(most_active_period[0] + 24 -
                    0.5, 24, facecolor='green', alpha=0.3)
        plt.axvspan(0, most_active_period[1] +
                    0.5, facecolor='green', alpha=0.3)
    elif most_active_period[1] > 23:
        plt.axvspan(most_active_period[0] - 0.5,
                    24, facecolor='green', alpha=0.3)
        plt.axvspan(0, most_active_period[1] -
                    24 + 0.5, facecolor='green', alpha=0.3)
    else:
        plt.axvspan(
            most_active_period[0] - 0.5, most_active_period[1] + 0.5, facecolor='green', alpha=0.3)

    plt.scatter(xs - 24, ys, c=ys, cmap=cmap, s=10)
    plt.vlines(most_active_hour, 0, max(ys)*1.05,
               colors='#ff6666', linestyles='dashed')

    plt.xlim(0, 24)
    plt.ylim(-0.5, max(ys)*1.05)
    plt.xticks(np.arange(0, 25, 4), [f'{i:02}:00' for i in range(0, 25, 4)])
    plt.yticks([])
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.gca().spines['left'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    plt.gca().spines['top'].set_visible(False)
    plt.gca().yaxis.set_visible(False)

    output = BytesIO()
    plt.savefig(output, format='png', bbox_inches='tight')
    output.seek(0)
    plt.close()
    return output


def plot_post_activity_year(post_day):
    offset = datetime(CURRENT_YEAR, 1, 1).weekday()
    activity = np.zeros(7*53)
    activity[offset:offset + len(post_day)] = post_day
    activity_matrix = np.reshape(activity, (-1, 7)).T
    activity_per_weekday = np.sum(activity_matrix, axis=1).astype(np.int32)
    activity_per_week = np.sum(activity_matrix, axis=0).astype(np.int32)

    g = sns.JointGrid(space=0, ratio=6)
    g.ax_joint.imshow(activity_matrix, cmap='Greens',
                      aspect='auto', origin='lower')

    g.ax_joint.spines['left'].set_visible(False)
    g.ax_joint.spines['right'].set_visible(False)

    month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May',
                    'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_first_days = [(datetime(CURRENT_YEAR, month, 1).timetuple(
    ).tm_yday+offset-1)/7-0.5 for month in range(1, 13)]

    g.ax_joint.set_xticks(month_first_days)
    g.ax_joint.set_xticklabels(month_labels)
    g.ax_joint.set_aspect('equal', adjustable='box')

    week_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    g.ax_joint.set_yticks(np.arange(7))

    g.ax_joint.set_yticklabels(
        week_labels, fontproperties=fm.FontProperties(family='monospace'))
    g.ax_joint.yaxis.set_ticks_position('none')

    sns.kdeplot(np.repeat(np.arange(len(activity_per_week)),
                activity_per_week), ax=g.ax_marg_x, color='green', fill=True)
    g.ax_marg_x.set_xlim(-0.5, 52.5)

    sns.histplot(y=np.arange(len(activity_per_weekday)), weights=activity_per_weekday,
                 ax=g.ax_marg_y,  bins=7, edgecolor='white', kde=True)
    g.ax_marg_y.yaxis.set_visible(False)
    g.ax_marg_y.spines['left'].set_visible(False)

    g.fig.set_size_inches(14, 2)

    output = BytesIO()
    plt.savefig(output, format='png', bbox_inches='tight')
    output.seek(0)
    plt.close()
    return output
