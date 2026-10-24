# Installing a build

## Before you start

- **Back up your projects** to a computer.
- **Keep Roland's original OS 1.01 file** so you can always go back. It is available from [Roland's MV-8800 support page](https://www.roland.com/au/support/by_product/mv-8800/updates_drivers/bc905792-2358-42b7-8952-a049c70add0e/), along with Roland's own update instructions.
- Use a reliable power supply. Do not switch off the MV-8800 while the system software is being written.

## 1. Pick a build

| Build | When to use it |
| --- | --- |
| **r13** | Fastest saves (about 1.5 s faster than r12_clean). Holds some save data in memory slightly longer; see the power-loss note in [KNOWN_ISSUES.md](KNOWN_ISSUES.md). |
| r12_clean | The most conservative patched build. |

## 2. Download and verify

On GitHub, open the `.PRG` file and click **Download raw file**. Then check it:

- The size must be exactly **4,194,304 bytes**.
- The SHA-256 must match [`SHA256SUMS.txt`](../SHA256SUMS.txt):

```text
Windows:        certutil -hashfile MV8800_r13.PRG SHA256
macOS / Linux:  shasum -a 256 MV8800_r13.PRG
```

| Build | SHA-256 |
| --- | --- |
| r13 | `3304b86e90211808ba704d8a8a7480f36ba45e6f4e7ab8bb28ceaf8b50adead7` |
| r12_clean | `2e8555db2afa8799790a311ca4ffaf2399a7c0771e643b150137f0212d78c8da` |

Do not install a file whose checksum does not match. A renamed ZIP file, a partial download or a file saved by a browser as a web page will all fail this check.

## 3. Install

1. Rename the verified file to `MV8800.PRG` (exactly that name).
2. Install it the same way as Roland's official OS 1.01 update, following Roland's instructions. Only the file is different.

In the tested setup (CF card in place of the internal hard drive), `MV8800.PRG` was copied to the root of the CF card and installed with the MV-8800's system update procedure.

## 4. Check it works

1. Load a project you know well and check that it plays normally.
2. Save it. Saves should be clearly faster than before.
3. Optional: copy a project folder to your computer before the update, then load and save it unchanged on the new build and compare the two with [`tools/project_checksums.py`](../tools/README.md). Every file should match. (Saving under a new name also changes `PROJECT_.MV0`, which holds the project name.)

## Going back

To return to the stock OS, or to switch between builds, install the other `MV8800.PRG` (Roland's original, r12_clean or r13) with the same procedure. Projects are compatible in both directions because the project file format is not changed.

## If the instrument does not start after an update

This has not happened during testing, but any firmware update carries this risk. Install Roland's original OS 1.01 again using Roland's update instructions. If the MV-8800 cannot reach its update mode at all, contact a Roland service center.
