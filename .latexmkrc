# Latexmk configuration for kaobook
# This ensures consistent builds across different environments

# Default to lualatex (recommended for kaobook)
$pdf_mode = 4;  # 4 = lualatex, 5 = xelatex, 1 = pdflatex

# Alternative: use xelatex
# $pdf_mode = 5;

# For pdflatex (limited font support):
# $pdf_mode = 1;

# Enable shell escape for minted, tikz externalize, etc.
$lualatex = 'lualatex -shell-escape -interaction=nonstopmode -file-line-error %O %S';
$xelatex = 'xelatex -shell-escape -interaction=nonstopmode -file-line-error %O %S';
$pdflatex = 'pdflatex -shell-escape -interaction=nonstopmode -file-line-error %O %S';

# Biber for bibliography (biblatex)
$biber = 'biber %O %S';
$bibtex_use = 2;  # 2 = run biber/bibtex when needed

# Glossaries support
add_cus_dep('glo', 'gls', 0, 'makeglossaries');
add_cus_dep('acn', 'acr', 0, 'makeglossaries');
sub makeglossaries {
    my ($base_name, $path) = fileparse($_[0]);
    my @args = ("makeglossaries", "-d", $path, $base_name);
    if ($path && -d $path) {
        return system(@args);
    }
    return system("makeglossaries", $base_name);
}
push @generated_exts, 'glo', 'gls', 'glg', 'acn', 'acr', 'alg';

# Nomenclature support
add_cus_dep('nlo', 'nls', 0, 'makenlo2nls');
sub makenlo2nls {
    system("makeindex -s nomencl.ist -o '$_[0].nls' '$_[0].nlo'");
}
push @generated_exts, 'nlo', 'nls';

# Index support
$makeindex = 'makeindex %O -o %D %S';

# Clean up auxiliary files
@generated_exts = (@generated_exts,
    'aux', 'bbl', 'bcf', 'blg', 'fdb_latexmk', 'fls',
    'idx', 'ilg', 'ind', 'lof', 'log', 'lot', 'out',
    'run.xml', 'toc', 'synctex.gz', 'snm', 'nav', 'vrb',
    'xdv', 'pytxcode'
);

# Maximum number of runs (prevent infinite loops)
$max_repeat = 5;

# Show warnings
$warnings_as_errors = 0;

# Preview mode (open PDF after compilation)
# $preview_mode = 1;
# $pdf_previewer = 'start';  # Windows
# $pdf_previewer = 'open';   # macOS
# $pdf_previewer = 'evince'; # Linux

# Output directory - compile from kaobook root, output to dissertation folder
$out_dir = 'dissertation';

# Ensure biber can find the references.bib
$ENV{'BIBINPUTS'} = './dissertation//:';
