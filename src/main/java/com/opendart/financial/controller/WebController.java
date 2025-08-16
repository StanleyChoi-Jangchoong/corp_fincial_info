package com.opendart.financial.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

/**
 * 웹 페이지 컨트롤러
 */
@Controller
public class WebController {
    
    /**
     * 메인 페이지
     */
    @GetMapping("/")
    public String index() {
        return "index";
    }
    
    /**
     * 검색 페이지
     */
    @GetMapping("/search")
    public String search() {
        return "search";
    }
}
