<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "xhtml1-strict.dtd">
<?
/*
 * Copyright (c) 2005 Benjamin Schweizer <gopher at h07 dot org>
 *                    http://www.redsheep.de/
 */
?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="<?php echo $conf['lang']?>"
 lang="<?php echo $conf['lang']?>" dir="<?php echo $lang['direction']?>">
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title><?php echo hsc($conf['title']) . '.' . $ID?></title>
    <meta name="author" content="Benjamin Schweizer, redsheep.de" />
    <meta name="robots" content="all" />
    <meta name="keywords" content="Benjamin Schweizer" />
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <?php tpl_metaheaders()?>
    <link rel="contents" href="index.html" type="text/html" title="Index">
    <link rel="icon" href="img/pipe.png" type="image/png" />
    <link rel="stylesheet" href="<?php echo DOKU_TPL?>css/screen.css" type="text/css" media="screen" title="Screen Stylesheet">
    <link rel="stylesheet" href="<?php echo DOKU_TPL?>css/print.css" type="text/css" media="print">
    <link rel="stylesheet" href="<?php echo DOKU_TPL?>css/content.css" type="text/css" media="all">
  </head>

  <body>
    <!-- h1 id="title"><?php tpl_link(wl($ID,'do=backlink'),$ID)?></h1 -->
    <h1 id="title"> grafity.<?php echo $ID?></h1>
    <!-- div id="subtitle"><?php tpl_breadcrumbs()?></div -->
    <div id="subtitle"><div id="search"><?php tpl_searchform()?></div>
    <?php tpl_youarehere()?>
 </div>
    <div id="toolbar">
      <div id="references">
        <?php /*old includehook*/ @include(dirname(__FILE__).'/references.html')?>
      </div>

      <div id="global">
        <?php
      if($conf['useacl']){
        if($_SERVER['REMOTE_USER']){
	  tpl_link(wl($ID,'do=logout'),$_SERVER['REMOTE_USER'] . ' log out');
	} else {
	  tpl_link(wl($ID,'do=login'),'Log in');
	}
      }
        ?>
        <?php tpl_link(wl($ID,'do=diff'),'Changes')?>
        <?php tpl_link(wl($ID,'do=backlink'),'Backlinks')?>
        <?php tpl_link(wl($ID,'do=recent'),'Recent')?>
        <?php tpl_link(wl($ID,'do=index'),'Sitemap')?>
      </div>
    </div>
    <div id="content">
      <div id="foo"><?php if($conf['useacl']&&$_SERVER['REMOTE_USER'])tpl_button('edit')?></div>
      <?php tpl_content()?>
      <!-- ?php tpl_pageinfo()? -->
    </div>
  </body>
</html>
