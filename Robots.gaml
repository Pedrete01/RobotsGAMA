/**
* Name: Robots
* Based on the internal empty template. 
* Author: pedro Abad Valero
* Tags: 
*/


model Robots

global {
	
	int nRobots <- 100;
	int agent_size <- 1;
	int episode <- 0;
	int iteracion <- 0 update: iteracion + 1;
	
	init {
		create robot number: nRobots;
	}
	
	reflex end1 when: robot all_match (each.color = #black){
		do pause;
	}
	
	reflex stop when: iteracion = 5000{
		do pause;
	}
	
	list<point> get_agents_pos {
	    list<point> agent_positions;
	    loop i over: robot {
	        agent_positions <- agent_positions + i.location;
	    }
	    return agent_positions;
	}
	
	action set_agents_vel(matrix<float> vt, matrix<float> vr){
		int n <- 0;
		loop i over: robot {
	        float t_velocity <- vt[n];
	        float r_velocity <- vr[n];
			n <- n + 1;
	        
	        ask i {
	        	do set_velocity(t_velocity, r_velocity);
	        }
	    }
	}
	
	list<point> get_agents_neigh {
	    list<point> agent_neigh;
	    loop i over: robot {
	        agent_neigh <- agent_neigh + i.get_closest_neighbord_pos();
	    }
	    return agent_neigh;
	}
	
	list<float> get_agents_angulo {
	    list<float> agent_angulo;
	    loop i over: robot {
	        agent_angulo <- agent_angulo + i.heading;
	    }
	    return agent_angulo;
	}
	
	action restart {
		iteracion <- 0;
		
		ask robot{
			do die;
		}
		
		create robot number: nRobots;
	}
	
	/*
	 * Python
	 * - Pos del agente
	 * - Pos del agente mas cercano
	 * - Angulo actual del agente
	 * 
	 * Debe decidir cual es el nuevo angulo 
	 */
}

species robot skills: [moving]{	
	
	rgb color <- #red;
	
	action set_velocity(float vt, float vr){
		do move speed: vt heading: vr;
    }
    
    point get_closest_neighbord_pos {
    	return agent_closest_to(self).location;
    }
	
	reflex move{
		if self.color != #black {
			if self.location distance_to get_closest_neighbord_pos() < 2.0{
				do move speed: 0.05 heading: heading + 45;
			}
			do move speed: 0.05 heading: heading + rnd(-5.0,5.0);
		}else{
			do move speed: 0.0 heading: heading;
		}
    }
    
    reflex collision {
    	list<robot> col <- list<robot>(agents at_distance(agent_size));
    	
    	ask col{
    		self.color <- #black;
    	}
    }
	
	aspect default {
		draw circle(agent_size) color:	self.color;
	}
}

species tatami {
	aspect base
	{
	  draw square(20) color: #black;
	}
}

experiment robots_move type: gui {
	float minimum_cycle_duration <- 0.05;
	output {				
		display map background:#white type:3d{ 
			species tatami aspect: base;
			species robot aspect: default;
		}
		monitor "Number of robots" value: nRobots;
	}
}

