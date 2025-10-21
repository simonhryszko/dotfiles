-- Disable netrw banner
vim.cmd("let g:netrw_banner = 0")

-- line numbers
vim.opt.nu = true
vim.opt.relativenumber = true

-- indentation
vim.opt.tabstop = 2
vim.opt.softtabstop = 2
vim.opt.shiftwidth = 2
vim.opt.expandtab = true
vim.opt.smartindent = true
vim.opt.wrap = false

-- backup and undo
vim.opt.swapfile = false
vim.opt.backup = false
vim.opt.undodir = os.getenv("HOME") .. "/.vim/undodir"
vim.opt.undofile = true

-- search
vim.opt.incsearch = true
vim.opt.inccommand = "split"
vim.opt.ignorecase = true
vim.opt.smartcase = true

-- UI
vim.opt.termguicolors = true
vim.opt.background = "dark"
vim.opt.scrolloff = 8
vim.opt.signcolumn = "yes"

-- folding (for nvim-ufo)
-- vim.o.foldenable = true
-- vim.o.foldmethod = "manual"
-- vim.o.foldlevel = 99
-- vim.o.foldcolumn = "0"

-- window splits
vim.opt.backspace = { "start", "eol", "indent" }
vim.opt.splitright = true
vim.opt.splitbelow = true

-- misc
vim.opt.isfname:append("@-@")
vim.opt.updatetime = 50
vim.opt.colorcolumn = "80"
vim.opt.clipboard:append("unnamedplus")
vim.opt.hlsearch = true
vim.opt.mouse = "a"
vim.g.editorconfig = true
